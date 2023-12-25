JELASTIC_API = "https://app.xapp.cloudmydc.com"
NODE_GROUP_CP = "cp"
NODE_GROUP_SQLDB = "sqldb"

NETBOX_SETTINGS = {
    "required": [
        "ALLOWED_HOSTS",
        "DB_CONN_MAX_AGE",
        "DB_DISABLE_SERVER_SIDE_CURSORS",
        "DB_HOST",
        "DB_NAME",
        "DB_PASSWORD",
        "DB_PORT",
        "DB_SSLMODE",
        "DB_USER",
        "DB_WAIT_TIMEOUT",
        "REDIS_CACHE_DATABASE",
        "REDIS_CACHE_HOST",
        "REDIS_CACHE_INSECURE_SKIP_TLS_VERIFY",
        "REDIS_CACHE_PASSWORD",
        "REDIS_CACHE_PORT",
        "REDIS_CACHE_SSL",
        "REDIS_CACHE_USERNAME",
        "REDIS_DATABASE",
        "REDIS_HOST",
        "REDIS_INSECURE_SKIP_TLS_VERIFY",
        "REDIS_PASSWORD",
        "REDIS_PORT",
        "REDIS_SSL",
        "REDIS_USERNAME",
    ],
    "system": [
        "BASE_PATH",
        "DEFAULT_LANGUAGE",
        "EMAIL_FROM",
        "EMAIL_PASSWORD",
        "EMAIL_PASSWORD",
        "EMAIL_PORT",
        "EMAIL_SERVER",
        "EMAIL_SSL_CERTFILE",
        "EMAIL_SSL_KEYFILE",
        "EMAIL_TIMEOUT",
        "EMAIL_USERNAME",
        "EMAIL_USE_SSL",
        "EMAIL_USE_TLS",
        "ENABLE_LOCALIZATION",
        "GIT_PATH",
        "HTTP_PROXIES",
        "INTERNAL_IPS",
        "JINJA2_FILTERS",
        "MEDIA_ROOT",
        "REPORTS_ROOT",
        "SCRIPTS_ROOT",
        "STORAGE_BACKEND",
        "STORAGE_CONFIG",
    ],
    "security": [
        "ALLOW_TOKEN_RETRIEVAL",
        "ALLOWED_URL_SCHEMES",
        "AUTH_PASSWORD_VALIDATORS",
        "CORS_ORIGIN_ALLOW_ALL",
        "CORS_ORIGIN_REGEX_WHITELIST",
        "CORS_ORIGIN_WHITELIST",
        "CSRF_COOKIE_NAME",
        "CSRF_COOKIE_SECURE",
        "CSRF_TRUSTED_ORIGINS",
        "LOGIN_PERSISTENCE",
        "LOGIN_REQUIRED",
        "LOGIN_TIMEOUT",
        "SECURE_SSL_REDIRECT",
    ],
    "remoteauth": ["REMOTE_AUTH_ENABLED"],
    "data": ["CUSTOM_VALIDATORS", "FIELD_CHOICES"],
    "default": [
        "DEFAULT_DASHBOARD",
        "DEFAULT_USER_PREFERENCES",
        "PAGINATE_COUNT",
        "POWERFEED_DEFAULT_AMPERAGE",
        "POWERFEED_DEFAULT_MAX_UTILIZATION",
        "POWERFEED_DEFAULT_VOLTAGE",
        "RACK_ELEVATION_DEFAULT_UNIT_HEIGHT",
        "RACK_ELEVATION_DEFAULT_UNIT_WIDTH",
    ],
    "plugins": ["PLUGINS", "PLUGINS_CONFIG"],
    "datetime": [
        "DATETIME_FORMAT",
        "DATE_FORMAT",
        "SHORT_DATETIME_FORMAT",
        "SHORT_DATE_FORMAT",
        "SHORT_TIME_FORMAT",
        "TIME_FORMAT",
        "TIME_ZONE",
    ],
    "misc": [
        "ADMINS",
        "BANNER_BOTTOM",
        "BANNER_LOGIN",
        "BANNER_TOP",
        "BANNER_MAINTENANCE",
        "CENSUS_REPORTING_ENABLED",
        "CHANGELOG_RETENTION",
        "DATA_UPLOAD_MAX_MEMORY_SIZE",
        "ENFORCE_GLOBAL_UNIQUE",
        "FILE_UPLOAD_MAX_MEMORY_SIZE",
        "GRAPHQL_ENABLED",
        "JOB_RETENTION",
        "MAINTENANCE_MODE",
        "MAPS_URL",
        "MAX_PAGE_SIZE",
        "METRICS_ENABLED",
        "PREFER_IPV4",
        "QUEUE_MAPPINGS",
        "RELEASE_CHECK_URL",
        "RQ_DEFAULT_TIMEOUT",
        "RQ_RETRY_INTERVAL",
        "RQ_RETRY_MAX",
    ],
    "development": [
        "DEBUG",
    ],
    "container": [
        "HOUSEKEEPING_INTERVAL",
        "LOGLEVEL",
        "MAX_DB_WAIT_TIME",
    ],
}

NETBOX_SUPERUSER_SETTINGS = ["SUPERUSER_NAME", "SUPERUSER_EMAIL", "SUPERUSER_PASSWORD"]