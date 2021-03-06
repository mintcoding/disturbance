# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-18 08:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0231_auto_20210305_1607'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='masterlistquestion',
            name='help_text_assessor_url',
        ),
        migrations.RemoveField(
            model_name='masterlistquestion',
            name='help_text_url',
        ),
        migrations.AlterField(
            model_name='masterlistquestion',
            name='answer_type',
            field=models.CharField(choices=[('text', 'Text'), ('radiobuttons', 'Radio button'), ('checkbox', 'Checkbox'), ('text_info', 'Text Info'), ('iframe', 'IFrame'), ('number', 'Number'), ('email', 'Email'), ('select', 'Select'), ('multi-select', 'Multi-select'), ('text_area', 'Text area'), ('label', 'Label'), ('section', 'Section'), ('declaration', 'Declaration'), ('file', 'File'), ('date', 'Date')], default='text', max_length=40, verbose_name='Answer Type'),
        ),
    ]
