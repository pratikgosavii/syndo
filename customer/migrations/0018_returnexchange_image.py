# Generated migration for ReturnExchange.image

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0017_remove_order_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnexchange',
            name='image',
            field=models.ImageField(blank=True, help_text='Image for return/exchange (e.g. product condition)', null=True, upload_to='return_exchange/'),
        ),
    ]
