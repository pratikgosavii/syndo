from django.apps import AppConfig


def _cleanup_orphan_fks(sender, **kwargs):
    """Auto-cleanup orphaned FK rows before any migration runs (prevents IntegrityError on SQLite)."""
    try:
        from django.db import connection
        if "sqlite" not in connection.settings_dict.get("ENGINE", ""):
            return  # SQLite-specific issue; skip for postgres etc.

        # Tables and FK columns that can hold orphaned user refs
        user_refs = [
            ("vendor_vendornotification", "user_id"),
            ("vendor_ordernotificationmessage", "user_id"),
        ]
        # Tables that can hold orphaned product refs
        product_refs = [
            ("vendor_stocktransaction", "product_id"),
            ("vendor_saleitem", "product_id"),
            ("vendor_purchaseitem", "product_id"),
            ("vendor_onlineorderledger", "product_id"),
            ("vendor_serial_imei_no", "product_id"),
            ("vendor_product_addon", "product_id"),
        ]

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            for table, col in user_refs:
                try:
                    cursor.execute(
                        f"DELETE FROM \"{table}\" WHERE \"{col}\" IS NOT NULL "
                        f"AND \"{col}\" NOT IN (SELECT id FROM \"users_user\")"
                    )
                    if cursor.rowcount > 0:
                        print(f"[pre_migrate] Cleaned {cursor.rowcount} orphans from {table}.{col}")
                except Exception:
                    pass
            for table, col in product_refs:
                try:
                    cursor.execute(
                        f"DELETE FROM \"{table}\" WHERE \"{col}\" IS NOT NULL "
                        f"AND \"{col}\" NOT IN (SELECT id FROM \"vendor_product\")"
                    )
                    if cursor.rowcount > 0:
                        print(f"[pre_migrate] Cleaned {cursor.rowcount} orphans from {table}.{col}")
                except Exception:
                    pass
            cursor.execute("PRAGMA foreign_keys = ON")
    except Exception as e:
        print(f"[pre_migrate] Orphan cleanup skipped: {e}")


class VendorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendor'

    def ready(self):
        import vendor.signals

        # Register pre_migrate cleanup so orphaned FK rows never block migrations
        from django.db.models.signals import pre_migrate
        pre_migrate.connect(_cleanup_orphan_fks, sender=self)
