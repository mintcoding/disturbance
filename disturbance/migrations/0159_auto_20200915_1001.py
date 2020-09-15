# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-09-15 02:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0158_auto_20200915_0948'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiarysite',
            name='latest_approval_link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='disturbance.ApiarySiteOnApproval'),
        ),
        migrations.AddField(
            model_name='apiarysite',
            name='latest_proposal_link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='disturbance.ApiarySiteOnProposal'),
        ),
    ]
