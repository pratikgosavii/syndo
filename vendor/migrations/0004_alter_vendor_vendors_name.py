# Generated by Django 5.1.4 on 2025-05-18 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0003_vendor_vendors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor_vendors',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
