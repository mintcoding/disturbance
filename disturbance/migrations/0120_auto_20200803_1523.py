# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-08-03 07:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0119_merge_20200803_1055'),
    ]

    operations = [
        migrations.RenameField(
            model_name='proposalrequirement',
            old_name='site_transfer_approval',
            new_name='apiary_approval',
        ),
    ]
