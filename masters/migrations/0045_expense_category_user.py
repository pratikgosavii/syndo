from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_devicetoken_user'),
        ('masters', '0044_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense_category',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='expense_categories', to='users.user'),
        ),
    ]

