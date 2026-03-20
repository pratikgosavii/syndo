# Idempotent cleanup after 0044 (and for DBs that already applied an older 0044).
# SQLite check_constraints validates the whole DB after migrations.

from django.db import migrations


def cleanup_orphan_fk_rows(apps, schema_editor):
    from django.contrib.auth import get_user_model
    from django.db import connection

    User = get_user_model()
    user_table = User._meta.db_table
    qn = connection.ops.quote_name

    product_refs = [
        ("vendor_stocktransaction", "product_id"),
        ("vendor_saleitem", "product_id"),
        ("vendor_purchaseitem", "product_id"),
        ("vendor_onlineorderledger", "product_id"),
        ("vendor_serial_imei_no", "product_id"),
        ("vendor_product_addon", "product_id"),
    ]

    user_refs = [
        ("vendor_vendornotification", "user_id"),
        ("vendor_ordernotificationmessage", "user_id"),
    ]

    with connection.cursor() as cursor:
        if "sqlite" in connection.settings_dict["ENGINE"]:
            cursor.execute("PRAGMA foreign_keys = OFF")

        for table, col in product_refs:
            try:
                cursor.execute(
                    f"""
                    DELETE FROM {qn(table)}
                    WHERE {qn(col)} IS NOT NULL
                      AND {qn(col)} NOT IN (SELECT id FROM {qn("vendor_product")})
                    """
                )
                n = cursor.rowcount
                if n and n > 0:
                    print(f"0045: deleted {n} from {table}.{col}")
            except Exception as e:
                print(f"0045: skip {table}.{col}: {e}")

        for table, col in user_refs:
            try:
                cursor.execute(
                    f"""
                    DELETE FROM {qn(table)}
                    WHERE {qn(col)} IS NOT NULL
                      AND {qn(col)} NOT IN (SELECT id FROM {qn(user_table)})
                    """
                )
                n = cursor.rowcount
                if n and n > 0:
                    print(f"0045: deleted {n} from {table}.{col} (missing user)")
            except Exception as e:
                print(f"0045: skip {table}.{col}: {e}")

        if "sqlite" in connection.settings_dict["ENGINE"]:
            cursor.execute("PRAGMA foreign_keys = ON")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0044_onlineordersettlement"),
    ]

    operations = [
        migrations.RunPython(cleanup_orphan_fk_rows, noop_reverse),
    ]
