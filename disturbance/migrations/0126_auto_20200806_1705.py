# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-08-06 09:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0125_apiarychecklistanswer_referral'),
    ]

    operations = [
        migrations.RenameField(
            model_name='apiarychecklistanswer',
            old_name='referral',
            new_name='apiary_referral',
        ),
    ]
