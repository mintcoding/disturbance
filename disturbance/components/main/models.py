from __future__ import unicode_literals
import os

from django.contrib.gis.db.models import MultiPolygonField
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from ledger.accounts.models import (
        EmailUser, 
        #Document, 
        RevisionedMixin
        )
from django.contrib.postgres.fields.jsonb import JSONField
from ledger_common import models as ledger_common_models


@python_2_unicode_compatible
class Region(ledger_common_models.AbstractRegion):
#class Region(models.Model):

    class Meta:
        #ordering = ['name']
        app_label = 'disturbance'


@python_2_unicode_compatible
class District(ledger_common_models.AbstractDistrict):
    region = models.ForeignKey('disturbance.Region', related_name='districts')

    class Meta:
        #ordering = ['name']
        app_label = 'disturbance'

class DistrictDbca(models.Model):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    district_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['object_id', ]
        app_label = 'disturbance'


class RegionDbca(models.Model):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    region_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['object_id', ]
        app_label = 'disturbance'


class CategoryDbca(models.Model):
    '''
    This model is used for defining the categories
    '''
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    category_name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        app_label = 'disturbance'


class WaCoast(models.Model):
    '''
    This model is used for validating if the apiary site is in the valid area
    '''
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    smoothed = models.BooleanField(default=False)

    class Meta:
        app_label = 'disturbance'


@python_2_unicode_compatible
class ApplicationType(models.Model):
    DISTURBANCE = 'Disturbance'
    POWERLINE_MAINTENANCE = 'Powerline Maintenance'
    APIARY = 'Apiary'
    TEMPORARY_USE = 'Temporary Use'
    SITE_TRANSFER = 'Site Transfer'

    APPLICATION_TYPES = (
        (DISTURBANCE, 'Disturbance'),
        (POWERLINE_MAINTENANCE, 'Powerline Maintenance'),
        (APIARY, 'Apiary'),
        (TEMPORARY_USE, 'Temporary Use'),
        (SITE_TRANSFER, 'Site Transfer'),
    )

    APIARY_APPLICATION_TYPES = (APIARY, TEMPORARY_USE, SITE_TRANSFER,)

    DOMAIN_USED_CHOICES = (
        ('das', 'DAS'),
        ('apiary', 'Apiary'),
    )

    # name = models.CharField(max_length=64, unique=True)
    name = models.CharField(
        verbose_name='Application Type name',
        max_length=64,
        choices=APPLICATION_TYPES,
    )
    order = models.PositiveSmallIntegerField(default=0)
    visible = models.BooleanField(default=True)
    application_fee = models.DecimalField(max_digits=6, decimal_places=2)
    oracle_code_application = models.CharField(max_length=50)
    is_gst_exempt = models.BooleanField(default=True)
    domain_used = models.CharField(max_length=40, choices=DOMAIN_USED_CHOICES, default=DOMAIN_USED_CHOICES[0][0])

    class Meta:
        ordering = ['order', 'name']
        app_label = 'disturbance'

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class ActivityMatrix(models.Model):
    # name = models.CharField(verbose_name='Activity matrix name', max_length=24, choices=application_type_choicelist(), default='Disturbance')
    name = models.CharField(verbose_name='Activity matrix name', max_length=24,
                            choices=[('Disturbance', u'Disturbance')], default='Disturbance')
    description = models.CharField(max_length=256, blank=True, null=True)
    schema = JSONField()
    replaced_by = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    ordered = models.BooleanField('Activities Ordered Alphabetically', default=False)

    class Meta:
        app_label = 'disturbance'
        unique_together = ('name', 'version')
        verbose_name_plural = "Activity matrix"

    def __str__(self):
        return '{} - v{}'.format(self.name, self.version)


@python_2_unicode_compatible
class Tenure(models.Model):
    name = models.CharField(max_length=255, unique=True)
    order = models.PositiveSmallIntegerField(default=0)
    application_type = models.ForeignKey(ApplicationType, related_name='tenure_app_types')

    class Meta:
        ordering = ['order', 'name']
        app_label = 'disturbance'

    def __str__(self):
        return '{}: {}'.format(self.name, self.application_type)


#@python_2_unicode_compatible
#class UserAction(models.Model):
#    who = models.ForeignKey(EmailUser, null=False, blank=False)
#    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
#    what = models.TextField(blank=False)
#
#    def __str__(self):
#        return "{what} ({who} at {when})".format(
#            what=self.what,
#            who=self.who,
#            when=self.when
#        )
#
#    class Meta:
#        abstract = True
#        app_label = 'disturbance'


class CommunicationsLogEntry(ledger_common_models.AbstractCommunicationsLogEntry):

    class Meta:
        app_label = 'disturbance'


@python_2_unicode_compatible
class Document(models.Model):
    name = models.CharField(max_length=255, blank=True,
                            verbose_name='name', help_text='')
    description = models.TextField(blank=True,
                                   verbose_name='description', help_text='')
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'disturbance'
        abstract = True

    @property
    def path(self):
        # return self.file.path
        return self._file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


@python_2_unicode_compatible
class SystemMaintenance(ledger_common_models.AbstractSystemMaintenance):

    class Meta:
        app_label = 'disturbance'


@python_2_unicode_compatible
class ApiaryGlobalSettings(models.Model):
    KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE = 'oracle_code_apiary_site_annural_rental_fee'  # ApplicationType object has an attribute 'oracle_code_application' to store oracle account code
                                                                                                  # However for the annual rental fee, there are not proposals, which means no ApplicationType objects related.
                                                                                                  # Therefore we store oracle account code for the annual site fee here.
    KEY_APIARY_SITES_LIST_TOKEN = 'apiary_sites_list_token'
    KEY_APIARY_LICENCE_TEMPLATE_FILE = 'apiary_licence_template_file'
    KEY_PRINT_DEED_POLL_URL = 'print_deed_poll_url'

    keys = (
        (KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE, 'Oracle code for the apiary site annual site fee'),
        (KEY_APIARY_SITES_LIST_TOKEN, 'Token to import the apiary sites list'),
        (KEY_APIARY_LICENCE_TEMPLATE_FILE, 'Apiary licence template file'),
        (KEY_PRINT_DEED_POLL_URL, 'URL of the deed poll'),
    )

    default_values = (
        (KEY_ORACLE_CODE_APIARY_SITE_ANNUAL_RENTAL_FEE, 'T1 EXEMPT'),
        (KEY_APIARY_SITES_LIST_TOKEN, 'abc123'),
        (KEY_APIARY_LICENCE_TEMPLATE_FILE, ''),
        (KEY_PRINT_DEED_POLL_URL, 'https://parks.dpaw.wa.gov.au/sites/default/files/downloads/know/DBCA%20apiary%20deed%20poll.pdf')
    )
    key = models.CharField(max_length=255, choices=keys, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255)
    _file = models.FileField(upload_to='apiary_licence_template', null=True, blank=True)

    class Meta:
        app_label = 'disturbance'
        verbose_name_plural = "Apiary Global Settings"

    def __str__(self):
        return self.key


@python_2_unicode_compatible
class GlobalSettings(models.Model):
    KEY_ASSESSMENT_REMINDER_DAYS = 'assessment_reminder_days'

    keys = (
        (KEY_ASSESSMENT_REMINDER_DAYS, 'Assessment reminder days'),
    )
    default_values = (
    )
    key = models.CharField(max_length=255, choices=keys, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = 'disturbance'
        verbose_name_plural = "Global Settings"

    def __str__(self):
        return self.key


class TemporaryDocumentCollection(models.Model):
    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'disturbance'


# temp document obj for generic file upload component
class TemporaryDocument(Document):
    temp_document_collection = models.ForeignKey(
        TemporaryDocumentCollection,
        related_name='documents')
    _file = models.FileField(max_length=255)

    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'disturbance'


import reversion
reversion.register(ApiaryGlobalSettings)
