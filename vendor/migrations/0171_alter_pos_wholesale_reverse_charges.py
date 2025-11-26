from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0170_purchase_advance_payment_amount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pos_wholesale',
            name='reverse_charges',
            field=models.BooleanField(default=False),
        ),
    ]

