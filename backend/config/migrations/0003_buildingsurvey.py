from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0002_alter_feeconfiguration_component'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildingSurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kobo_id', models.IntegerField(unique=True)),
                ('kobo_uuid', models.UUIDField(unique=True)),
                ('submission_time', models.DateTimeField(blank=True, null=True)),
                ('enumerator_id', models.CharField(blank=True, max_length=50)),
                ('survey_date', models.DateField(blank=True, null=True)),
                ('locality', models.CharField(blank=True, max_length=200)),
                ('ward', models.CharField(blank=True, max_length=10)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('existing_street_name', models.CharField(blank=True, max_length=200)),
                ('proposed_street_name', models.CharField(blank=True, max_length=200)),
                ('existing_house_number', models.CharField(blank=True, max_length=50)),
                ('proposed_auto_number', models.CharField(blank=True, max_length=50)),
                ('building_use', models.CharField(blank=True, choices=[('residential', 'Residential'), ('commercial', 'Commercial'), ('mixed', 'Mixed'), ('institutional', 'Institutional'), ('other', 'Other')], max_length=20)),
                ('building_type', models.CharField(blank=True, choices=[('detached', 'Detached'), ('semi_detached', 'Semi-Detached'), ('flat', 'Flat'), ('bungalow', 'Bungalow'), ('storey_building', 'Storey Building'), ('others', 'Others')], max_length=20)),
                ('building_type_other', models.CharField(blank=True, max_length=200)),
                ('number_of_floors', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('number_of_flats', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('number_of_shops', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('compound_fence', models.BooleanField(blank=True, null=True)),
                ('occupancy_type', models.CharField(blank=True, choices=[('owner_occupied', 'Owner Occupied'), ('tenant', 'Tenant'), ('vacant', 'Vacant'), ('under_construction', 'Under Construction')], max_length=20)),
                ('primary_access_type', models.CharField(blank=True, choices=[('tarred_road', 'Tarred Road'), ('untarred_road', 'Untarred Road'), ('footpath', 'Footpath'), ('waterway', 'Waterway')], max_length=20)),
                ('vehicle_accessible', models.BooleanField(blank=True, null=True)),
                ('electricity_connection', models.BooleanField(blank=True, null=True)),
                ('water_supply', models.CharField(blank=True, choices=[('borehole', 'Borehole'), ('public_tap', 'Public Tap'), ('none', 'None')], max_length=20)),
                ('waste_collection', models.CharField(blank=True, choices=[('regular', 'Regular'), ('irregular', 'Irregular'), ('none', 'None')], max_length=20)),
                ('nearby_landmark', models.CharField(blank=True, max_length=500)),
                ('land_title_type', models.CharField(blank=True, max_length=100)),
                ('owner_name', models.CharField(blank=True, max_length=200)),
                ('contact_number', models.CharField(blank=True, max_length=50)),
                ('land_size', models.CharField(blank=True, max_length=100)),
                ('photo_url', models.URLField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'building_surveys',
                'ordering': ['kobo_id'],
            },
        ),
    ]
