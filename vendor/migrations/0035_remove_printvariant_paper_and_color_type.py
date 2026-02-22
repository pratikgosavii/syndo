# Generated manually - Remove paper and color_type from PrintVariant

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0034_invoice_settings_terms_and_conditions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='printvariant',
            name='paper',
        ),
        migrations.RemoveField(
            model_name='printvariant',
            name='color_type',
        ),
    ]
