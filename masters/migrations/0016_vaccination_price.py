# Generated by Django 5.1.4 on 2025-04-13 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0015_cat_breed'),
    ]

    operations = [
        migrations.AddField(
            model_name='vaccination',
            name='price',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
    ]
