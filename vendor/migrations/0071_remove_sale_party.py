# Generated by Django 5.1.4 on 2025-07-18 11:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0070_vendor_bank_balance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sale',
            name='party',
        ),
    ]
