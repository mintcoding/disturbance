# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-04 02:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wl_main', '0023_auto_20161026_1716'),
    ]

    operations = [
        migrations.RenameField(
            model_name='variant',
            old_name='product_code',
            new_name='product_title',
        ),
        migrations.RenameField(
            model_name='wildlifelicencetype',
            old_name='product_code',
            new_name='product_title',
        ),
    ]