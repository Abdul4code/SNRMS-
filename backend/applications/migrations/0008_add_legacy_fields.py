from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0007_add_awaiting_renewal_payment_confirmation'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='is_legacy',
            field=models.BooleanField(
                default=False,
                help_text='Applicant had a manual certificate before digital registration',
            ),
        ),
        migrations.AddField(
            model_name='application',
            name='legacy_certificate',
            field=models.FileField(blank=True, null=True, upload_to='legacy_certificates/'),
        ),
    ]
