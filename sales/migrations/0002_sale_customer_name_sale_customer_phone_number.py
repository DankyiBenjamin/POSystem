# Generated by Django 5.1.5 on 2025-06-06 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='customer_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='customer_phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
