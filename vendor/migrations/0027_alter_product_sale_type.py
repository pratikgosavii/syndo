# Generated by Django 5.1.4 on 2025-05-21 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0026_alter_product_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sale_type',
            field=models.CharField(choices=[('offline', 'Offline Only'), ('online', 'Online Only'), ('both', 'Both Online & Offline')], default='offline', max_length=10),
        ),
    ]
