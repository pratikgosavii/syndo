# Fixes SQLite IntegrityError on migrate: rows referencing deleted vendor_product.id
# (SQLite check_constraints validates the whole DB after schema changes).

from django.db import migrations


def cleanup_orphan_product_fk_rows(apps, schema_editor):
    """
    Remove rows that point to non-existent vendor_product.id.
    """
    from django.db import connection

    tables = [
        ("vendor_stocktransaction", "product_id"),
        ("vendor_saleitem", "product_id"),
        ("vendor_purchaseitem", "product_id"),
        ("vendor_onlineorderledger", "product_id"),
        ("vendor_serial_imei_no", "product_id"),
        ("vendor_product_addon", "product_id"),
    ]

    with connection.cursor() as cursor:
        if "sqlite" in connection.settings_dict["ENGINE"]:
            cursor.execute("PRAGMA foreign_keys = OFF")

        for table, col in tables:
            try:
                cursor.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE {col} IS NOT NULL
                      AND {col} NOT IN (SELECT id FROM vendor_product)
                    """
                )
                n = cursor.rowcount
                if n and n > 0:
                    print(f"cleanup_orphan_product_fk_rows: deleted {n} from {table}.{col}")
            except Exception as e:
                print(f"cleanup_orphan_product_fk_rows: skip {table}.{col}: {e}")

        if "sqlite" in connection.settings_dict["ENGINE"]:
            cursor.execute("PRAGMA foreign_keys = ON")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0044_onlineordersettlement"),
    ]

    operations = [
        migrations.RunPython(cleanup_orphan_product_fk_rows, noop_reverse),
    ]
