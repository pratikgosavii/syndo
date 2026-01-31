# Generated manually for storing GST/Bank API response for admin review

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0030_remove_offer_product_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor_store',
            name='gstin_response_data',
            field=models.JSONField(blank=True, help_text='Stored GSTIN API response for admin review', null=True),
        ),
        migrations.AddField(
            model_name='vendor_store',
            name='bank_response_data',
            field=models.JSONField(blank=True, help_text='Stored Bank API response for admin review', null=True),
        ),
    ]
