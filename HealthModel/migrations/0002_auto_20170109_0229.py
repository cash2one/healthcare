# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-01-09 02:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HealthModel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='deleteFlag',
            field=models.CharField(default='0', max_length=10),
        ),
        migrations.AddField(
            model_name='membership',
            name='endDate',
            field=models.CharField(default='9999/12/31', max_length=10),
        ),
        migrations.AddField(
            model_name='membership',
            name='startDate',
            field=models.CharField(default='0000/01/01', max_length=10),
        ),
    ]
