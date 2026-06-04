from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qms', '0006_qmsdocument_ai_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qmsdocument',
            name='file',
            field=models.FileField(blank=True, upload_to='qms_documents/'),
        ),
    ]
