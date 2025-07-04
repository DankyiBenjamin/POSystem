# Generated by Django 5.1.5 on 2025-06-03 20:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('total_stock_added', models.IntegerField(default=0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('shop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.shop')),
            ],
        ),
        migrations.CreateModel(
            name='Restock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_added', models.IntegerField()),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='restocks', to='inventory.item')),
            ],
        ),
    ]
