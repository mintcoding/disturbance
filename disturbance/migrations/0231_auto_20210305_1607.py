# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-05 08:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0230_auto_20210305_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='masterlistquestion',
            name='answer_type',
            field=models.CharField(choices=[('text', 'Text'), ('radiobuttons', 'Radio button'), ('checkbox', 'Checkbox'), ('text_info', 'Text Info'), ('iframe', 'IFrame'), ('number', 'Number'), ('email', 'Email'), ('select', 'Select'), ('multi-select', 'Multi-elect'), ('text_area', 'Text area'), ('label', 'Label'), ('section', 'Section'), ('declaration', 'Declaration'), ('file', 'File'), ('date', 'Date')], default='text', max_length=40, verbose_name='Answer Type'),
        ),
    ]
