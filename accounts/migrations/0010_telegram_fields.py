from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_add_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='telegram_chat_id',
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.AddField(
            model_name='customuser',
            name='telegram_link_token',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
