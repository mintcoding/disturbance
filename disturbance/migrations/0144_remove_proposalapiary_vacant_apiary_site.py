# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-09-04 02:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0143_remove_apiarysite_proposal_apiary_ids'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proposalapiary',
            name='vacant_apiary_site',
        ),
    ]
