# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-10-06 01:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0186_wacoast'),
    ]

    operations = [
        migrations.AddField(
            model_name='wacoast',
            name='smoothed',
            field=models.BooleanField(default=False),
        ),
    ]
