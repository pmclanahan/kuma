# Django settings for kitsune project.
import os
import logging

from tower import ugettext_lazy as _lazy

import sumo_locales

DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOG_LEVEL = logging.DEBUG

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kitsune', # Or path to database file if using sqlite3.
        'USER': '', # Not used with sqlite3.
        'PASSWORD': '', # Not used with sqlite3.
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    }
}

DATABASE_ROUTERS = ('multidb.MasterSlaveRouter',)

# Put the aliases for your slave databases in this list
SLAVE_DATABASES = []

# Cache Settings
#CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
#CACHE_PREFIX = 'sumo:'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# Supported languages
SUMO_LANGUAGES = (
    'ar', 'as', 'bg', 'bn-BD', 'bn-IN', 'ca', 'cs', 'da', 'de', 'el', 'en-US',
    'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'fur', 'fy-NL', 'ga-IE', 'gl',
    'gu-IN', 'he', 'hi-IN', 'hr', 'hu', 'id', 'is', 'it', 'ja', 'kk', 'kn',
    'ko', 'lt', 'mk', 'mn', 'mr', 'ms', 'nb-NO', 'nl', 'no', 'oc', 'pa-IN',
    'pl', 'pt-BR', 'pt-PT', 'rm', 'ro', 'ru', 'rw', 'si', 'sk', 'sl',
    'sq', 'sr-CYRL', 'sr-LATN', 'sv-SE', 'ta-LK', 'te', 'th', 'tr',
    'uk', 'vi', 'zh-CN', 'zh-TW',
)

LANGUAGES = dict([(i.lower(), sumo_locales.languages[i].native)
                 for i in SUMO_LANGUAGES])

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

TEXT_DOMAIN = 'k-messages'

SITE_ID = 1
SITE_TITLE = _lazy(u'Firefox Support', 'site_title')


# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = ('media',)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'sumo.context_processors.title',
)

MIDDLEWARE_CLASSES = (
    'sumo.middleware.LocaleURLMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'kitsune.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'tower',
    'sumo',
    'search',
)

# Extra apps for testing
if DEBUG:
    INSTALLED_APPS += (
        'django_extensions',
        'django_nose',
        'test_utils',
    )   

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from caching.base import cache
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',],
              'finalize': lambda x: x if x is not None else ''}
    if 'memcached' in cache.scheme and not settings.DEBUG:
        # We're passing the _cache object directly to jinja because
        # Django can't store binary directly; it enforces unicode on it.
        # Details: http://jinja.pocoo.org/2/documentation/api#bytecode-cache
        # and in the errors you get when you try it the other way.
        bc = jinja2.MemcachedBytecodeCache(cache._cache,
                                           "%sj2:" % settings.CACHE_PREFIX)
        config['cache_size'] = -1  # Never clear the cache
        config['bytecode_cache'] = bc
    return config

# Tells the extract script what files to look for l10n in and what function
# handles the extraction.  The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'lhtml': [
        ('**/templates/**.lhtml',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/*.js', 'javascript'),
    ],
}

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS=True

# Directory storying myspell dictionaries (with trailing slash)
DICT_DIR = '/usr/share/myspell/'
# Path to a file with a list of custom words.
WORD_LIST = path('configs/words.txt')

#
# Connection information for Sphinx search
SPHINX_HOST = '127.0.0.1'
SPHINX_PORT = 3312

SPHINX_INDEXER = '/usr/bin/indexer'
SPHINX_SEARCHD = '/usr/bin/searchd'
SPHINX_CONFIG_PATH = path('configs/sphinx/sphinx.conf')

#
# Sphinx results tweaking
SEARCH_FORUM_MIN_AGE = 7 # age before which decay doesn't apply, in days
SEARCH_FORUM_HALF_LIFE = 14 # controls the decay rate, in days
SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

#
# Search default settings
# comma-separated tuple of category IDs
SEARCH_DEFAULT_CATEGORIES = (1, 17, 18, -3,)
SEARCH_DEFAULT_FORUMS = (1,) # default forum ID (eg: 1 on sumo, 5 on mosumo)
SEARCH_SUMMARY_LENGTH = 275
# because of markup cleanup, search summaries lengths vary quite a bit
# so we extract longer excerpts and perform truncation to the length above
SEARCH_SUMMARY_LENGTH_MULTIPLIER = 1.3