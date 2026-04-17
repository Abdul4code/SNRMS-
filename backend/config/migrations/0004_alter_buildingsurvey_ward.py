from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0003_buildingsurvey'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildingsurvey',
            name='ward',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
