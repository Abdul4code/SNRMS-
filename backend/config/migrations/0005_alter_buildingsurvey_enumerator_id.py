from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0004_alter_buildingsurvey_ward'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildingsurvey',
            name='enumerator_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
