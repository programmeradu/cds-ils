# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# CDS-ILS is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""Default configuration for CDS-ILS.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

import copy
import os
from datetime import timedelta

from invenio_app.config import APP_DEFAULT_SECURE_HEADERS
from invenio_app_ils.config import \
    CELERY_BEAT_SCHEDULE as ILS_CELERY_BEAT_SCHEDULE
from invenio_app_ils.config import RECORDS_REST_ENDPOINTS
from invenio_app_ils.locations.api import LOCATION_PID_TYPE
from invenio_app_ils.patrons.api import PATRON_PID_TYPE, AnonymousPatron
from invenio_oauthclient.contrib import cern_openid
from invenio_records_rest.schemas.fields import SanitizedUnicode
from invenio_records_rest.utils import deny_all
from marshmallow.fields import Bool, List

from .literature.covers import build_cover_urls
from .patrons.api import Patron
from .patrons.permissions import views_permissions_factory


def _(x):
    """Identity function used to trigger string extraction."""
    return x


def _parse_env_bool(var_name, default=None):
    if str(os.environ.get(var_name)).lower() == "true":
        return True
    elif str(os.environ.get(var_name)).lower() == "false":
        return False
    return default


###############################################################################
# Search
###############################################################################
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.environ.get("ELASTICSEARCH_PORT", "9200"))
ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_URL_PREFIX = os.environ.get("ELASTICSEARCH_URL_PREFIX", "")
ELASTICSEARCH_USE_SSL = _parse_env_bool("ELASTICSEARCH_USE_SSL")
ELASTICSEARCH_VERIFY_CERTS = _parse_env_bool("ELASTICSEARCH_VERIFY_CERTS")

es_host_params = {"host": ELASTICSEARCH_HOST, "port": ELASTICSEARCH_PORT}
if ELASTICSEARCH_USER and ELASTICSEARCH_PASSWORD:
    es_host_params["http_auth"] = (ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)
if ELASTICSEARCH_URL_PREFIX:
    es_host_params["url_prefix"] = ELASTICSEARCH_URL_PREFIX
if ELASTICSEARCH_USE_SSL is not None:
    es_host_params["use_ssl"] = ELASTICSEARCH_USE_SSL
if ELASTICSEARCH_VERIFY_CERTS is not None:
    es_host_params["verify_certs"] = ELASTICSEARCH_VERIFY_CERTS

SEARCH_ELASTIC_HOSTS = [es_host_params]
"""Elasticsearch hosts configuration."""

###############################################################################
# Rate limiting
###############################################################################
#: Storage for rate limiter.
RATELIMIT_STORAGE_URL = "redis://localhost:6379/3"

###############################################################################
# I18N
###############################################################################
#: Default language
BABEL_DEFAULT_LANGUAGE = "en"
#: Default time zone
BABEL_DEFAULT_TIMEZONE = "Europe/Zurich"
#: Other supported languages (do not include the default language in list).
I18N_LANGUAGES = [
    # ('fr', _('French'))
]

###############################################################################
# Theme
###############################################################################
#: Global base template.
BASE_TEMPLATE = "invenio_theme/page.html"
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = "invenio_theme/page_cover.html"
#: Footer base template.
FOOTER_TEMPLATE = "invenio_theme/footer.html"
#: Header base template.
HEADER_TEMPLATE = "invenio_theme/header.html"
#: Settings base template.
SETTINGS_TEMPLATE = "invenio_theme/page_settings.html"

THEME_FRONTPAGE = False

###############################################################################
# Email
###############################################################################
#: Email address for support.
SUPPORT_EMAIL = "cds.support@cern.ch"
#: Management email for internal notifications.
MANAGEMENT_EMAIL = "cds.internal@cern.ch"
#: Disable email sending by default.
MAIL_SUPPRESS_SEND = True
#: Email address for email notification sender.
MAIL_NOTIFY_SENDER = "library.desk@cern.ch"

###############################################################################
# Accounts
###############################################################################
#: Email address used as sender of account registration emails.
SECURITY_EMAIL_SENDER = SUPPORT_EMAIL
#: Email subject for account registration emails.
SECURITY_EMAIL_SUBJECT_REGISTER = _("Welcome to the CERN Library Catalogue!")
#: Redis session storage URL.
ACCOUNTS_SESSION_REDIS_URL = "redis://localhost:6379/1"
#: Enable session/user id request tracing. This feature will add X-Session-ID
#: and X-User-ID headers to HTTP response. You MUST ensure that NGINX (or other
#: proxies) removes these headers again before sending the response to the
#: client. Set to False, in case of doubt.
ACCOUNTS_USERINFO_HEADERS = True

###############################################################################
# Celery configuration
###############################################################################
BROKER_URL = "amqp://guest:guest@localhost:5672/"
#: URL of message broker for Celery (default is RabbitMQ).
CELERY_BROKER_URL = "amqp://guest:guest@localhost:5672/"
#: URL of backend for result storage (default is Redis).
CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
#: Scheduled tasks configuration (aka cronjobs).
CELERY_BEAT_SCHEDULE = {
    **ILS_CELERY_BEAT_SCHEDULE,  # Parent config
    "synchronize_users": {
        "task": "cds_ils.ldap.tasks.synchronize_users_task",
        "schedule": timedelta(days=1),
    },
}

###############################################################################
# Database
###############################################################################
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://cds-ils:cds-ils@localhost/cds-ils"
)

###############################################################################
# JSONSchemas
###############################################################################
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_HOST = "cds-ils.cern.ch"

###############################################################################
# Flask configuration
###############################################################################
# See details on
# http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

#: Secret key - each installation (dev, production, ...) needs a separate key.
#: It should be changed before deploying.
SECRET_KEY = "CHANGE_ME"
#: Max upload size for form data via application/mulitpart-formdata.
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MiB
#: Sets cookie with the secure flag by default
SESSION_COOKIE_SECURE = True
#: Since HAProxy and Nginx route all requests no matter the host header
#: provided, the allowed hosts variable is set to localhost. In production it
#: should be set to the correct host and it is strongly recommended to only
#: route correct hosts to the application.
APP_ALLOWED_HOSTS = [
    os.environ.get("ALLOWED_HOST", "localhost"),
    "127.0.0.1",
    os.environ.get("HOSTNAME", ""),  # fix disallowed host error during /ping
]

# if you need to render the Debugtoolbar, add 'unsafe-inline':
#   "script-src": ["'self'", "'unsafe-inline'"],
#   "style-src": ["'self'", "'unsafe-inline'"],
APP_DEFAULT_SECURE_HEADERS["content_security_policy"] = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "object-src": ["'self'"],
    "img-src": ["'self'"],
    "style-src": ["'self'"],
    "font-src": [
        "'self'",
        "data:",
        "https://fonts.gstatic.com",
        "https://fonts.googleapis.com",
    ],
}

###############################################################################
# Debug
###############################################################################
# Flask-DebugToolbar is by default enabled when the application is running in
# debug mode. More configuration options are available at
# https://flask-debugtoolbar.readthedocs.io/en/latest/#configuration

DEBUG = False
DEBUG_TB_ENABLED = True
#: Switches off intercept of redirects by Flask-DebugToolbar.
DEBUG_TB_INTERCEPT_REDIRECTS = False

###############################################################################
# Sentry
###############################################################################
LOGGING_SENTRY_LEVEL = "WARNING"
"""Sentry logging level."""

LOGGING_SENTRY_PYWARNINGS = False
"""Enable logging of Python warnings to Sentry."""

LOGGING_SENTRY_CELERY = False
"""Configure Celery to send logging to Sentry."""

SENTRY_DSN = None
"""Set SENTRY_DSN environment variable."""

SENTRY_CONFIG = {"environment": os.environ.get("SENTRY_ENVIRONMENT", "dev")}

try:
    # Try to get the release tag
    from raven import fetch_git_sha

    SENTRY_CONFIG["release"] = fetch_git_sha(
        os.environ.get("DEPLOYMENT_INSTANCE_PATH")
    )
except Exception:
    pass

###############################################################################
# OAuth
###############################################################################
OAUTH_REMOTE_APP_NAME = "cern_openid"
# common
_OAUTH_REMOTE_APP_COMMON = dict(
    base_url=os.environ.get(
        "OAUTH_CERN_OPENID_BASE_URL",
        "https://keycloak-qa.cern.ch/auth/realms/cern",
    ),
    access_token_url=os.environ.get(
        "OAUTH_CERN_OPENID_ACCESS_TOKEN_URL",
        "https://keycloak-qa.cern.ch/auth/realms/cern/"
        "protocol/openid-connect/token",
    ),
    authorize_url=os.environ.get(
        "OAUTH_CERN_OPENID_AUTHORIZE_URL",
        "https://keycloak-qa.cern.ch/auth/realms/cern/"
        "protocol/openid-connect/auth",
    ),
)
OAUTHCLIENT_CERN_OPENID_ALLOWED_ROLES = ["cern-user", "librarian", "admin"]
CERN_APP_OPENID_CREDENTIALS = dict(
    consumer_key=os.environ.get(
        "OAUTH_CERN_OPENID_CLIENT_ID", "localhost-cds-ils"
    ),
    consumer_secret=os.environ.get(
        "OAUTH_CERN_OPENID_CLIENT_SECRET",
        "<change_me>",
    ),
)
USERPROFILES_EXTEND_SECURITY_FORMS = True
###############################################################################
# non-REST
OAUTH_REMOTE_APP = copy.deepcopy(cern_openid.REMOTE_APP)
OAUTH_REMOTE_APP["params"].update(_OAUTH_REMOTE_APP_COMMON)
OAUTHCLIENT_REMOTE_APPS = dict(
    cern_openid=OAUTH_REMOTE_APP,
)
###############################################################################
# REST
logout_redirect_url = os.environ.get("INVENIO_SPA_HOST",
                                     "https://127.0.0.1:3000/")
OAUTH_REMOTE_REST_APP = copy.deepcopy(cern_openid.REMOTE_REST_APP)
OAUTH_REMOTE_REST_APP["params"].update(_OAUTH_REMOTE_APP_COMMON)
OAUTH_REMOTE_REST_APP["logout_url"] = os.environ.get(
    "OAUTH_CERN_OPENID_LOGOUT_URL",
    "https://keycloak-qa.cern.ch/auth/realms/cern/"
    "protocol/openid-connect/logout/?redirect_uri={}".format(
        logout_redirect_url),
)
OAUTH_REMOTE_REST_APP["authorized_redirect_url"] = (
    os.environ.get("INVENIO_SPA_HOST", "https://127.0.0.1:3000") + "/login"
)
OAUTH_REMOTE_REST_APP["disconnect_redirect_url"] = os.environ.get(
    "INVENIO_SPA_HOST", "https://127.0.0.1:3000"
)
OAUTH_REMOTE_REST_APP["error_redirect_url"] = (
    os.environ.get("INVENIO_SPA_HOST", "https://127.0.0.1:3000") + "/login"
)

OAUTHCLIENT_REST_REMOTE_APPS = dict(cern_openid=OAUTH_REMOTE_REST_APP)

###############################################################################
# Flask-Security
###############################################################################
# Disable user registration
SECURITY_REGISTERABLE = False
SECURITY_RECOVERABLE = False
SECURITY_CONFIRMABLE = False
SECURITY_CHANGEABLE = False
PERMANENT_SESSION_LIFETIME = timedelta(1)
SECURITY_LOGIN_SALT = "CHANGE_ME"
SECURITY_POST_LOGOUT_VIEW = '/api/cern_openid/logout/'
# Override login template to remove local logins
# Use this in deployed envs, when having login via CERN SSO only
# OAUTHCLIENT_LOGIN_USER_TEMPLATE = "cds_ils/login_user.html"

###############################################################################
# LDAP configuration
###############################################################################
CDS_ILS_LDAP_URL = "ldap://xldap.cern.ch"

###############################################################################
# OAI-PMH
###############################################################################
OAISERVER_ID_PREFIX = "oai:cds-ils:"

###############################################################################
# Migrator configuration
###############################################################################
MIGRATOR_RECORDS_DUMPLOADER_CLS = (
    "cds_ils.migrator.records:CDSDocumentDumpLoader"
)
MIGRATOR_RECORDS_DUMP_CLS = "cds_ils.migrator.records:CDSRecordDump"

###############################################################################
# JSONSchemas
###############################################################################
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_HOST = "cds-books.com"

# whitelist schemas for migration
JSONSCHEMAS_SCHEMAS = [
    "acquisition",
    "document_requests",
    "documents",
    "eitems",
    "ill",
    "internal_locations",
    "items",
    "invenio_opendefinition",
    "invenio_records_files",
    "loans",
    "locations",
    "series",
    "vocabularies",
]

###############################################################################
# RECORDS REST
###############################################################################
RECORDS_REST_ENDPOINTS[PATRON_PID_TYPE]["record_class"] = Patron
RECORDS_REST_ENDPOINTS[LOCATION_PID_TYPE]["create_permission_factory_imp"] \
    = deny_all
RECORDS_REST_ENDPOINTS[LOCATION_PID_TYPE]["delete_permission_factory_imp"] \
    = deny_all

###############################################################################
# Literature covers Syndetic client ID
###############################################################################
CDS_ILS_SYNDETIC_CLIENT = "CHANGE_ME"

###############################################################################
# ILS overridden
###############################################################################
ILS_VIEWS_PERMISSIONS_FACTORY = views_permissions_factory

ILS_LITERATURE_COVER_URLS_BUILDER = build_cover_urls

# Namespaces for fields added to the metadata schema
ILS_RECORDS_METADATA_NAMESPACES = {
    "document": {
        "unit": {"@context": "https://cern.ch/unit/terms"},
        "standard_review": {
            "@context": "https://cern.ch/standard_review/terms"
        },
    }
}

# Fields added to the metadata schema.
ILS_RECORDS_METADATA_EXTENSIONS = {
    "document": {
        "unit:accelerator": {
            "elasticsearch": "keyword",
            "marshmallow": List(SanitizedUnicode()),
        },
        "unit:curated_relation": {
            "elasticsearch": "boolean",
            "marshmallow": Bool(),
        },
        "unit:experiment": {
            "elasticsearch": "keyword",
            "marshmallow": List(SanitizedUnicode()),
        },
        "unit:institution": {
            "elasticsearch": "keyword",
            "marshmallow": List(SanitizedUnicode()),
        },
        "unit:project": {
            "elasticsearch": "keyword",
            "marshmallow": SanitizedUnicode(),
        },
        "unit:study": {
            "elasticsearch": "keyword",
            "marshmallow": List(SanitizedUnicode()),
        },
        "standard_review:applicability": {
            "elasticsearch": "keyword",
            "marshmallow": List(SanitizedUnicode()),
        },
        "standard_review:standard_validity": {
            "elasticsearch": "keyword",
            "marshmallow": SanitizedUnicode(required=True),
        },
        "standard_review:checkdate": {
            "elasticsearch": "date",
            "marshmallow": SanitizedUnicode(),
        },
        "standard_review:comment": {
            "elasticsearch": "text",
            "marshmallow": SanitizedUnicode(),
        },
        "standard_review:expert": {
            "elasticsearch": "keyword",
            "marshmallow": SanitizedUnicode(),
        },
    }
}

ILS_CIRCULATION_MAIL_TEMPLATES = {
    "librarian_footer": "cds_librarian_footer.html"
}

ILS_PATRON_ANONYMOUS_CLASS = AnonymousPatron
