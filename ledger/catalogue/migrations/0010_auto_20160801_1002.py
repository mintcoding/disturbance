# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-01 02:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0009_product_oracle_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='oracle_code',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name=b'Oracle Code'),
        ),
    ]