# Generated by Django 5.1.4 on 2025-05-17 17:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0029_rename_opening_stock_product_stock'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='stock',
            new_name='opening_stock',
        ),
    ]
