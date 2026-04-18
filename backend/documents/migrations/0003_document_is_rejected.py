from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_alter_document_document_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='is_rejected',
            field=models.BooleanField(default=False),
        ),
    ]
