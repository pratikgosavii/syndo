# Generated by Django 5.1.4 on 2025-06-03 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0043_alter_printvariant_color_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printvariant',
            name='price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
    ]
