# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-05-13 03:30
from __future__ import unicode_literals

import disturbance.components.compliances.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('disturbance', '0038_auto_20200513_1049'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiarySiteFeeRemainder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_of_sites_left', models.SmallIntegerField(default=0)),
                ('datetime_created', models.DateTimeField(auto_now_add=True)),
                ('datetime_expired', models.DateTimeField(blank=True, null=True)),
                ('apiary_site_fee_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='disturbance.ApiarySiteFeeType')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('site_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='disturbance.SiteCategory')),
            ],
        ),
        migrations.AlterField(
            model_name='compliancedocument',
            name='_file',
            field=models.FileField(max_length=500, upload_to=disturbance.components.compliances.models.update_proposal_complaince_filename),
        ),
    ]