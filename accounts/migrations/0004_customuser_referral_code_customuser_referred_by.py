import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def generate_referral_codes(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    for user in CustomUser.objects.all():
        user.referral_code = uuid.uuid4().hex[:8].upper()
        user.save(update_fields=['referral_code'])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_expertprofile_is_verified_expertprofile_verified_at"),
    ]

    operations = [
        # 1. Avval unique=False bilan qo'shamiz (bo'sh string bilan)
        migrations.AddField(
            model_name="customuser",
            name="referral_code",
            field=models.CharField(blank=True, max_length=12, default=''),
        ),
        # 2. Mavjud foydalanuvchilarga unique kod generatsiya qilamiz
        migrations.RunPython(generate_referral_codes, migrations.RunPython.noop),
        # 3. Endi unique constraint qo'shamiz
        migrations.AlterField(
            model_name="customuser",
            name="referral_code",
            field=models.CharField(blank=True, max_length=12, unique=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="referred_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referrals",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
