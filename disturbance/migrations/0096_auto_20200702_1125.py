# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-07-02 03:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0095_annualrentfee_annualrentfeeinvoice'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AnnualRentFee',
            new_name='AnnualRentalFee',
        ),
        migrations.RenameModel(
            old_name='AnnualRentFeeInvoice',
            new_name='AnnualRentalFeeInvoice',
        ),
    ]
