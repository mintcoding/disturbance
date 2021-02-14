from django.core.exceptions import ImproperlyConfigured

import os, hashlib
import confy
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger.settings_base import *


ROOT_URLCONF = 'disturbance.urls'
SITE_ID = 1
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SUPERVISOR_STOP_CMD = env('SUPERVISOR_STOP_CMD')
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24) # hours
DISABLE_EMAIL = env('DISABLE_EMAIL', False)
MEDIA_APP_DIR = env('MEDIA_APP_DIR', 'das')
MEDIA_APIARY_DIR = env('MEDIA_APIARY_DIR', 'apiary')
SPATIAL_DATA_DIR = env('SPATIAL_DATA_DIR', 'spatial_data')
ANNUAL_RENTAL_FEE_GST_EXEMPT = True

INSTALLED_APPS += [
    'reversion_compare',
    'bootstrap3',
    'disturbance',
    'disturbance.components.main',
    'disturbance.components.organisations',
    'disturbance.components.users',
    'disturbance.components.proposals',
    'disturbance.components.approvals',
    'disturbance.components.compliances',
    'disturbance.components.das_payments',
    'taggit',
    'rest_framework',
    'rest_framework_datatables',
    'rest_framework_gis',
    'reset_migrations',
    'ckeditor',
    'ledger_common',
]

ADD_REVERSION_ADMIN=True

# maximum number of days allowed for a booking
WSGI_APPLICATION = 'disturbance.wsgi.application'

'''REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'disturbance.perms.OfficerPermission',
    )
}'''

#REST_FRAMEWORK = {
#    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
#    #'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#        'PAGE_SIZE': 5
#}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    #'DEFAULT_FILTER_BACKENDS': (
    #    'rest_framework_datatables.filters.DatatablesFilterBackend',
    #),
    #'DEFAULT_PAGINATION_CLASS': 'rest_framework_datatables.pagination.DatatablesPageNumberPagination',
    #'PAGE_SIZE': 20,
}


MIDDLEWARE_CLASSES += [
    'disturbance.middleware.BookingTimerMiddleware',
    'disturbance.middleware.FirstTimeNagScreenMiddleware',
    'disturbance.middleware.RevisionOverrideMiddleware',
    'disturbance.middleware.DomainDetectMiddleware',
]

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance','components','organisations', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance','components','emails', 'templates'))
TEMPLATES[0]['OPTIONS']['context_processors'].append('disturbance.context_processors.apiary_url')
del BOOTSTRAP3['css_url']
#BOOTSTRAP3 = {
#    'jquery_url': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
#    'base_url': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
#    'css_url': None,
#    'theme_url': None,
#    'javascript_url': None,
#    'javascript_in_head': False,
#    'include_jquery': False,
#    'required_css_class': 'required-form-field',
#    'set_placeholder': False,
#}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'disturbance', 'cache'),
    }
}
STATIC_ROOT=os.path.join(BASE_DIR, 'staticfiles_ds')
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'disturbance', 'static')))
DEV_STATIC = env('DEV_STATIC',False)
DEV_STATIC_URL = env('DEV_STATIC_URL')
if DEV_STATIC and not DEV_STATIC_URL:
    raise ImproperlyConfigured('If running in DEV_STATIC, DEV_STATIC_URL has to be set')
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Department details
SYSTEM_NAME = env('SYSTEM_NAME', 'Disturbance Approval System')
APIARY_SYSTEM_NAME = env('APIARY_SYSTEM_NAME', 'Apiary System')
SYSTEM_NAME_SHORT = env('SYSTEM_NAME_SHORT', 'DAS')
SITE_PREFIX = env('SITE_PREFIX')
SITE_DOMAIN = env('SITE_DOMAIN')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', SYSTEM_NAME_SHORT.lower() + '@' + SITE_DOMAIN).lower()
APIARY_SUPPORT_EMAIL = env('APIARY_SUPPORT_EMAIL', SUPPORT_EMAIL).lower()
DEP_URL = env('DEP_URL','www.' + SITE_DOMAIN)
DEP_PHONE = env('DEP_PHONE','(08) 9219 9000')
DEP_PHONE_SUPPORT = env('DEP_PHONE_SUPPORT','(08) 9219 9000')
DEP_FAX = env('DEP_FAX','(08) 9423 8242')
DEP_POSTAL = env('DEP_POSTAL','Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env('DEP_NAME','Department of Biodiversity, Conservation and Attractions')
DEP_NAME_SHORT = env('DEP_NAME_SHORT','DBCA')
SITE_URL = env('SITE_URL', 'https://' + '.'.join([SITE_PREFIX, SITE_DOMAIN]).strip('.'))
PUBLIC_URL=env('PUBLIC_URL', SITE_URL)
EMAIL_FROM = env('EMAIL_FROM', 'no-reply@' + SITE_DOMAIN).lower()
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@' + SITE_DOMAIN).lower()
ADMIN_GROUP = env('ADMIN_GROUP', 'Disturbance Admin')
APIARY_ADMIN_GROUP = 'Apiary Admin'
DAS_APIARY_ADMIN_GROUP = 'DAS-Apiary Admin'
APIARY_PAYMENTS_OFFICERS_GROUP = 'Apiary Payments Officers'
CRON_EMAIL = env('CRON_EMAIL', 'cron@' + SITE_DOMAIN).lower()
TENURE_SECTION = env('TENURE_SECTION', None)
ASSESSMENT_REMINDER_DAYS = env('ASSESSMENT_REMINDER_DAYS', 15)

OSCAR_BASKET_COOKIE_OPEN = 'das_basket'
PAYMENT_SYSTEM_ID = env('PAYMENT_SYSTEM_ID', 'S517')
PS_PAYMENT_SYSTEM_ID = PAYMENT_SYSTEM_ID
PAYMENT_SYSTEM_PREFIX = env('PAYMENT_SYSTEM_PREFIX', PAYMENT_SYSTEM_ID.replace('S','0')) # '0517'
os.environ['LEDGER_PRODUCT_CUSTOM_FIELDS'] = "('ledger_description','quantity','price_incl_tax','price_excl_tax','oracle_code')"
APIARY_URL = env('APIARY_URL', [])
CRON_NOTIFICATION_EMAIL = env('CRON_NOTIFICATION_EMAIL', NOTIFICATION_EMAIL).lower()

BASE_URL=env('BASE_URL')



CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        #'width': 300,
        'width': '100%',
    },
    'awesome_ckeditor': {
        'toolbar': 'Basic',
    },
}

BUILD_TAG = env('BUILD_TAG', hashlib.md5(os.urandom(32)).hexdigest())  # URL of the Dev app.js served by webpack & express
DEV_APP_BUILD_URL = env('DEV_APP_BUILD_URL')  # URL of the Dev app.js served by webpack & express
GEOCODING_ADDRESS_SEARCH_TOKEN = env('GEOCODING_ADDRESS_SEARCH_TOKEN', 'ACCESS_TOKEN_NOT_FOUND')
RESTRICTED_RADIUS = 3000  # unit: [m]
DBCA_ABN = '38 052 249 024'
if env('CONSOLE_EMAIL_BACKEND', False):
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


SITE_STATUS_DRAFT = 'draft'
SITE_STATUS_PENDING = 'pending'
SITE_STATUS_APPROVED = 'approved'
SITE_STATUS_DENIED = 'denied'
SITE_STATUS_CURRENT = 'current'
SITE_STATUS_NOT_TO_BE_REISSUED = 'not_to_be_reissued'
SITE_STATUS_SUSPENDED = 'suspended'
SITE_STATUS_TRANSFERRED = 'transferred'
SITE_STATUS_VACANT = 'vacant'
SITE_STATUS_DISCARDED = 'discarded'
BASE_EMAIL_TEXT = ''
BASE_EMAIL_HTML = ''

# This is either 'das'/'apiary'
# default: 'das'
# This value is determined at the middleware, DomainDetectMiddleware by where the request comes from
DOMAIN_DETECTED = 'das'
HTTP_HOST_FOR_TEST = 'localhost:8071'

# Additional logging for commercialoperator
LOGGING['loggers']['disturbance'] = {
            'handlers': ['file'],
            'level': 'INFO'
        }


