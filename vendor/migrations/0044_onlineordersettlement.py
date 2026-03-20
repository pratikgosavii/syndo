from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def cleanup_orphan_product_fk_rows(apps, schema_editor):
    """
    Run before CreateModel so SQLite check_constraints passes (orphan stock rows etc.).
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
                    print(f"0044: cleaned {n} orphan row(s) from {table}.{col}")
            except Exception as e:
                print(f"0044: skip {table}.{col}: {e}")

        if "sqlite" in connection.settings_dict["ENGINE"]:
            cursor.execute("PRAGMA foreign_keys = ON")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0043_super_catalogue_food_type_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(cleanup_orphan_product_fk_rows, noop_reverse),
        migrations.CreateModel(
            name="OnlineOrderSettlement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("description", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "settled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_online_order_settlements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="online_order_settlements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
