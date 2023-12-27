JELASTIC_API = "https://app.xapp.cloudmydc.com"
NETBOX_JPS_REPO = "https://raw.githubusercontent.com/Onemind-Services-LLC/netbox-jps/feat/pypi"  # TODO: change to master
NODE_GROUP_CP = "cp"
NODE_GROUP_SQLDB = "sqldb"

SECTION_REQUIRED = None
SECTION_SYSTEM = "System"
SECTION_SECURITY = "Security"
SECTION_REMOTEAUTH = "Remote Authentication"
SECTION_DATA = "Data"
SECTION_DEFAULT = "Default"
SECTION_DATETIME = "Date/Time"
SECTION_MISC = "Miscellaneous"
SECTION_DEVELOPMENT = "Development"
SECTION_CONTAINER = "Container"

NETBOX_SETTINGS = {
    SECTION_REQUIRED: [
        {
            "ALLOWED_HOSTS": {
                "required": True,
                "help_text": "List of valid hostnames for this server",
                "label": "Allowed Hosts",
                "placeholder": "['netbox.example.com', 'localhost']",
            }
        },
        {
            "DB_CONN_MAX_AGE": {
                "required": False,
                "help_text": "Maximum age of database connections, in seconds",
                "label": "DB Connection Max Age",
                "placeholder": "300",
                "field_type": "NumberInput",
            }
        },
        {
            "DB_DISABLE_SERVER_SIDE_CURSORS": {
                "required": False,
                "help_text": "Disable server-side cursors",
                "label": "DB Disable Server Side Cursors",
                "placeholder": "False",
            }
        },
        {
            "DB_HOST": {
                "required": True,
                "help_text": "Database server hostname or IP address",
                "label": "DB Host",
                "placeholder": "localhost",
            }
        },
        {
            "DB_NAME": {
                "required": True,
                "help_text": "Database name",
                "label": "DB Name",
                "placeholder": "netbox",
            }
        },
        {
            "DB_PASSWORD": {
                "required": True,
                "help_text": "Database user password",
                "label": "DB Password",
                "placeholder": "password",
            }
        },
        {
            "DB_PORT": {
                "required": False,
                "help_text": "Database server port",
                "label": "DB Port",
                "placeholder": "5432",
                "field_type": "NumberInput",
            }
        },
        {
            "DB_SSLMODE": {
                "required": False,
                "help_text": "Database SSL mode",
                "label": "DB SSL Mode",
                "placeholder": "require",
            }
        },
        {
            "DB_USER": {
                "required": True,
                "help_text": "Database username",
                "label": "DB User",
                "placeholder": "netbox",
            }
        },
        {
            "DB_WAIT_TIMEOUT": {
                "required": False,
                "help_text": "Database connection wait timeout, in seconds",
                "label": "DB Wait Timeout",
                "placeholder": "300",
            }
        },
        {
            "REDIS_HOST": {
                "required": True,
                "help_text": "Redis server hostname or IP address",
                "label": "Redis Host",
                "placeholder": "redis",
            }
        },
        {
            "REDIS_INSECURE_SKIP_TLS_VERIFY": {
                "required": False,
                "help_text": "Skip TLS verification when connecting to Redis",
                "label": "Redis Insecure Skip TLS Verify",
                "placeholder": "False",
            }
        },
        {
            "REDIS_PASSWORD": {
                "required": False,
                "help_text": "Redis server password",
                "label": "Redis Password",
                "placeholder": "password",
            }
        },
        {
            "REDIS_PORT": {
                "required": True,
                "help_text": "Redis server port",
                "label": "Redis Port",
                "placeholder": "6379",
            }
        },
        {
            "REDIS_SSL": {
                "required": False,
                "help_text": "Use SSL when connecting to Redis",
                "label": "Redis SSL",
                "placeholder": "False",
            }
        },
        {
            "REDIS_USERNAME": {
                "required": False,
                "help_text": "Redis server username",
                "label": "Redis Username",
                "placeholder": "username",
            }
        },
    ],
    SECTION_SYSTEM: [
        {
            "BASE_PATH": {
                "required": False,
                "help_text": "Base path for URL patterns",
                "label": "Base Path",
                "placeholder": "/",
            }
        },
        {
            "DEFAULT_LANGUAGE": {
                "required": False,
                "help_text": "Default language code",
                "label": "Default Language",
                "placeholder": "en",
            }
        },
        {
            "EMAIL_FROM": {
                "required": False,
                "help_text": "Default email sender address",
                "label": "Email From",
                "placeholder": "NetBox <netbox.example.com>",
            }
        },
        {
            "EMAIL_PASSWORD": {
                "required": False,
                "help_text": "SMTP server password",
                "label": "Email Password",
                "placeholder": "password",
            }
        },
        {
            "EMAIL_PORT": {
                "required": False,
                "help_text": "SMTP server port",
                "label": "Email Port",
                "placeholder": "25",
                "field_type": "NumberInput",
            }
        },
        {
            "EMAIL_SERVER": {
                "required": False,
                "help_text": "SMTP server hostname or IP address",
                "label": "Email Server",
                "placeholder": "localhost",
            }
        },
        {
            "EMAIL_SSL_CERTFILE": {
                "required": False,
                "help_text": "SMTP SSL certificate file",
                "label": "Email SSL Certfile",
                "placeholder": "/path/to/certfile",
            }
        },
        {
            "EMAIL_SSL_KEYFILE": {
                "required": False,
                "help_text": "SMTP SSL key file",
                "label": "Email SSL Keyfile",
                "placeholder": "/path/to/keyfile",
            }
        },
        {
            "EMAIL_TIMEOUT": {
                "required": False,
                "help_text": "SMTP server timeout, in seconds",
                "label": "Email Timeout",
                "placeholder": "10",
            }
        },
        {
            "EMAIL_USERNAME": {
                "required": False,
                "help_text": "SMTP server username",
                "label": "Email Username",
                "placeholder": "username",
            }
        },
        {
            "EMAIL_USE_SSL": {
                "required": False,
                "help_text": "Use SSL when connecting to SMTP server",
                "label": "Email Use SSL",
                "placeholder": "False",
            }
        },
        {
            "EMAIL_USE_TLS": {
                "required": False,
                "help_text": "Use TLS when connecting to SMTP server",
                "label": "Email Use TLS",
                "placeholder": "False",
            }
        },
        {
            "ENABLE_LOCALIZATION": {
                "required": False,
                "label": "Enable Localization",
                "placeholder": "False",
            }
        },
        {
            "GIT_PATH": {
                "required": False,
                "help_text": "Path to git executable",
                "label": "Git Path",
                "placeholder": "/usr/bin/git",
            }
        },
        {
            "HTTP_PROXIES": {
                "required": False,
                "help_text": "Dictionary of HTTP proxies",
                "label": "HTTP Proxies",
                "placeholder": "{'http': 'http://proxy.example.com:3128'}",
            }
        },
        {
            "INTERNAL_IPS": {
                "required": False,
                "help_text": "List of internal IP addresses",
                "label": "Internal IPs",
                "placeholder": "['127.0.0.1']",
            }
        },
        {
            "JINJA2_FILTERS": {
                "required": False,
                "help_text": "Dictionary of Jinja2 filters",
                "label": "Jinja2 Filters",
                "placeholder": "{'filter_name': 'path.to.filter'}",
            }
        },
        {
            "MEDIA_ROOT": {
                "required": False,
                "help_text": "Absolute filesystem path to media files",
                "label": "Media Root",
                "placeholder": "/opt/netbox/netbox/media",
            }
        },
        {
            "REPORTS_ROOT": {
                "required": False,
                "help_text": "Absolute filesystem path to reports",
                "label": "Reports Root",
                "placeholder": "/opt/netbox/netbox/reports",
            }
        },
        {
            "SCRIPTS_ROOT": {
                "required": False,
                "help_text": "Absolute filesystem path to custom scripts",
                "label": "Scripts Root",
                "placeholder": "/opt/netbox/netbox/scripts",
            }
        },
        {
            "STORAGE_BACKEND": {
                "required": False,
                "help_text": "Storage backend for file attachments",
                "label": "Storage Backend",
                "placeholder": "django.core.files.storage.FileSystemStorage",
            }
        },
        {
            "STORAGE_CONFIG": {
                "required": False,
                "help_text": "Configuration parameters for the storage backend",
                "label": "Storage Config",
                "placeholder": "{'location': '/var/netbox/media'}",
            }
        },
    ],
    SECTION_SECURITY: [
        {
            "ALLOW_TOKEN_RETRIEVAL": {
                "required": False,
                "help_text": "Allow retrieval of user tokens in API or UI",
                "label": "Allow Token Retrieval",
                "placeholder": "False",
            }
        },
        {
            "ALLOWED_URL_SCHEMES": {
                "required": False,
                "help_text": "List of allowed URL schemes",
                "label": "Allowed URL Schemes",
                "placeholder": "['http', 'https']",
            }
        },
        {
            "AUTH_PASSWORD_VALIDATORS": {
                "required": False,
                "help_text": "List of password validators",
                "label": "Auth Password Validators",
                "placeholder": "[]",
            }
        },
        {
            "CORS_ORIGIN_ALLOW_ALL": {
                "required": False,
                "help_text": "Allow all CORS origins",
                "label": "CORS Origin Allow All",
                "placeholder": "False",
            }
        },
        {
            "CORS_ORIGIN_REGEX_WHITELIST": {
                "required": False,
                "help_text": "List of CORS origin regex patterns",
                "label": "CORS Origin Regex Whitelist",
                "placeholder": "[]",
            }
        },
        {
            "CORS_ORIGIN_WHITELIST": {
                "required": False,
                "help_text": "List of CORS origins",
                "label": "CORS Origin Whitelist",
                "placeholder": "[]",
            }
        },
        {
            "CSRF_COOKIE_NAME": {
                "required": False,
                "help_text": "Name of the CSRF cookie",
                "label": "CSRF Cookie Name",
                "placeholder": "csrftoken",
            }
        },
        {
            "CSRF_COOKIE_SECURE": {
                "required": False,
                "help_text": "Require HTTPS for CSRF cookie",
                "label": "CSRF Cookie Secure",
                "placeholder": "False",
            }
        },
        {
            "CSRF_TRUSTED_ORIGINS": {
                "required": False,
                "help_text": "List of trusted origins for CSRF",
                "label": "CSRF Trusted Origins",
                "placeholder": "[]",
            }
        },
        {
            "LOGIN_PERSISTENCE": {
                "required": False,
                "help_text": "Enable session persistence after browser restart",
                "label": "Login Persistence",
                "placeholder": "False",
            }
        },
        {
            "LOGIN_REQUIRED": {
                "required": False,
                "help_text": "Require authentication to access any data",
                "label": "Login Required",
                "placeholder": "False",
            }
        },
        {
            "LOGIN_TIMEOUT": {
                "required": False,
                "help_text": "Session timeout, in seconds",
                "label": "Login Timeout",
                "placeholder": "1209600",
            }
        },
        {
            "SECURE_SSL_REDIRECT": {
                "required": False,
                "help_text": "Redirect all non-HTTPS requests to HTTPS",
                "label": "Secure SSL Redirect",
                "placeholder": "False",
            }
        },
    ],
    SECTION_REMOTEAUTH: [
        {
            "REMOTE_AUTH_ENABLED": {
                "required": False,
                "help_text": "Enable remote authentication",
                "label": "Remote Auth Enabled",
                "placeholder": "False",
            }
        }
    ],
    SECTION_DATA: [
        {
            "CUSTOM_VALIDATORS": {
                "required": False,
                "help_text": "List of custom data validators",
                "label": "Custom Validators",
                "placeholder": "[]",
            }
        },
        {
            "FIELD_CHOICES": {
                "required": False,
                "help_text": "List of custom field choices",
                "label": "Field Choices",
                "placeholder": "[]",
            }
        },
    ],
    SECTION_DEFAULT: [
        {
            "DEFAULT_DASHBOARD": {
                "required": False,
                "help_text": "Default dashboard for users",
                "label": "Default Dashboard",
                "field_type": "Textarea",
            }
        },
        {
            "DEFAULT_USER_PREFERENCES": {
                "required": False,
                "help_text": "Default user preferences",
                "label": "Default User Preferences",
                "field_type": "Textarea",
            }
        },
        {
            "PAGINATE_COUNT": {
                "required": False,
                "help_text": "Default number of objects to display per page",
                "label": "Paginate Count",
                "placeholder": "50",
                "field_type": "NumberInput",
            }
        },
        {
            "POWERFEED_DEFAULT_AMPERAGE": {
                "required": False,
                "help_text": "Default power feed amperage",
                "label": "Powerfeed Default Amperage",
                "placeholder": "20",
                "field_type": "NumberInput",
            }
        },
        {
            "POWERFEED_DEFAULT_MAX_UTILIZATION": {
                "required": False,
                "help_text": "Default power feed maximum utilization",
                "label": "Powerfeed Default Max Utilization",
                "placeholder": "80",
                "field_type": "NumberInput",
            }
        },
        {
            "POWERFEED_DEFAULT_VOLTAGE": {
                "required": False,
                "help_text": "Default power feed voltage",
                "label": "Powerfeed Default Voltage",
                "placeholder": "120",
                "field_type": "NumberInput",
            }
        },
        {
            "RACK_ELEVATION_DEFAULT_UNIT_HEIGHT": {
                "required": False,
                "help_text": "Default rack elevation unit height",
                "label": "Rack Elevation Default Unit Height",
                "placeholder": "44",
                "field_type": "NumberInput",
            }
        },
        {
            "RACK_ELEVATION_DEFAULT_UNIT_WIDTH": {
                "required": False,
                "help_text": "Default rack elevation unit width",
                "label": "Rack Elevation Default Unit Width",
                "placeholder": "50",
                "field_type": "NumberInput",
            }
        },
    ],
    SECTION_DATETIME: [
        {
            "DATETIME_FORMAT": {
                "required": False,
                "help_text": "Default datetime format",
                "label": "Datetime Format",
                "placeholder": "N j, Y, H:i:s T",
            }
        },
        {
            "DATE_FORMAT": {
                "required": False,
                "help_text": "Default date format",
                "label": "Date Format",
                "placeholder": "N j, Y",
            }
        },
        {
            "SHORT_DATETIME_FORMAT": {
                "required": False,
                "help_text": "Default short datetime format",
                "label": "Short Datetime Format",
                "placeholder": "m/d/Y P",
            }
        },
        {
            "SHORT_DATE_FORMAT": {
                "required": False,
                "help_text": "Default short date format",
                "label": "Short Date Format",
                "placeholder": "m/d/Y",
            }
        },
        {
            "SHORT_TIME_FORMAT": {
                "required": False,
                "help_text": "Default short time format",
                "label": "Short Time Format",
                "placeholder": "H:i:s",
            }
        },
        {
            "TIME_FORMAT": {
                "required": False,
                "help_text": "Default time format",
                "label": "Time Format",
                "placeholder": "H:i:s",
            }
        },
        {
            "TIME_ZONE": {
                "required": False,
                "help_text": "Default time zone",
                "label": "Time Zone",
                "placeholder": "UTC",
            }
        },
    ],
    SECTION_MISC: [
        {
            "ADMINS": {
                "required": False,
                "help_text": "List of NetBox administrators",
                "label": "Admins",
                "placeholder": "[('NetBox Admin', 'admin@example.com')]",
            }
        },
        {
            "BANNER_BOTTOM": {
                "required": False,
                "help_text": "Bottom banner text",
                "label": "Banner Bottom",
                "placeholder": "Banner text",
                "field_type": "Textarea",
            }
        },
        {
            "BANNER_LOGIN": {
                "required": False,
                "help_text": "Login banner text",
                "label": "Banner Login",
                "placeholder": "Banner text",
                "field_type": "Textarea",
            }
        },
        {
            "BANNER_TOP": {
                "required": False,
                "help_text": "Top banner text",
                "label": "Banner Top",
                "placeholder": "Banner text",
                "field_type": "Textarea",
            }
        },
        {
            "BANNER_MAINTENANCE": {
                "required": False,
                "help_text": "Maintenance banner text",
                "label": "Banner Maintenance",
                "placeholder": "Banner text",
                "field_type": "Textarea",
            }
        },
        {
            "CENSUS_REPORTING_ENABLED": {
                "required": False,
                "help_text": "Enable census reporting",
                "label": "Census Reporting Enabled",
                "placeholder": "False",
            }
        },
        {
            "CHANGELOG_RETENTION": {
                "required": False,
                "help_text": "Change log retention policy, in days",
                "label": "Changelog Retention",
                "placeholder": "90",
            }
        },
        {
            "DATA_UPLOAD_MAX_MEMORY_SIZE": {
                "required": False,
                "help_text": "Maximum size of file uploads, in bytes",
                "label": "Data Upload Max Memory Size",
                "placeholder": "2621440",
            }
        },
        {
            "ENFORCE_GLOBAL_UNIQUE": {
                "required": False,
                "help_text": "Enforce global uniqueness of IP addresses",
                "label": "Enforce Global Unique",
                "placeholder": "False",
            }
        },
        {
            "FILE_UPLOAD_MAX_MEMORY_SIZE": {
                "required": False,
                "help_text": "Maximum size of file uploads, in bytes",
                "label": "File Upload Max Memory Size",
                "placeholder": "2621440",
            }
        },
        {
            "GRAPHQL_ENABLED": {
                "required": False,
                "help_text": "Enable GraphQL API",
                "label": "GraphQL Enabled",
                "placeholder": "False",
            }
        },
        {
            "JOB_RETENTION": {
                "required": False,
                "help_text": "Job retention policy, in days",
                "label": "Job Retention",
                "placeholder": "365",
            }
        },
        {
            "MAINTENANCE_MODE": {
                "required": False,
                "help_text": "Enable maintenance mode",
                "label": "Maintenance Mode",
                "placeholder": "False",
            }
        },
        {
            "MAPS_URL": {
                "required": False,
                "help_text": "URL to a map tile server",
                "label": "Maps URL",
                "placeholder": "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
            }
        },
        {
            "MAX_PAGE_SIZE": {
                "required": False,
                "help_text": "Maximum page size for paginated results",
                "label": "Max Page Size",
                "placeholder": "1000",
            }
        },
        {
            "METRICS_ENABLED": {
                "required": False,
                "help_text": "Enable metrics reporting",
                "label": "Metrics Enabled",
                "placeholder": "False",
            }
        },
        {
            "PREFER_IPV4": {
                "required": False,
                "help_text": "Prefer IPv4 addresses over IPv6",
                "label": "Prefer IPv4",
                "placeholder": "True",
            }
        },
        {
            "QUEUE_MAPPINGS": {
                "required": False,
                "help_text": "Dictionary of queue mappings",
                "label": "Queue Mappings",
                "placeholder": "{'queue_name': 'queue_name'}",
            }
        },
        {
            "RELEASE_CHECK_URL": {
                "required": False,
                "help_text": "URL for release check",
                "label": "Release Check URL",
                "placeholder": "https://api.github.com/repos/netbox-community/netbox/releases",
            }
        },
        {
            "RQ_DEFAULT_TIMEOUT": {
                "required": False,
                "help_text": "Default timeout for RQ jobs, in seconds",
                "label": "RQ Default Timeout",
                "placeholder": "300",
            }
        },
        {
            "RQ_RETRY_INTERVAL": {
                "required": False,
                "help_text": "Interval between RQ job retries, in seconds",
                "label": "RQ Retry Interval",
                "placeholder": "60",
            }
        },
        {
            "RQ_RETRY_MAX": {
                "required": False,
                "help_text": "Maximum number of RQ job retries",
                "label": "RQ Retry Max",
                "placeholder": "3",
            }
        },
    ],
    SECTION_DEVELOPMENT: [
        {
            "DEBUG": {
                "required": False,
                "help_text": "Enable debugging mode",
                "label": "Debug",
                "placeholder": "False",
            }
        },
        {
            "DEVELOPER": {
                "required": False,
                "help_text": "Enable developer mode, use with caution",
                "label": "Developer",
                "placeholder": "False",
            }
        },
    ],
    SECTION_CONTAINER: [
        {
            "HOUSEKEEPING_INTERVAL": {
                "required": False,
                "help_text": "Interval between housekeeping tasks, in seconds",
                "label": "Housekeeping Interval",
                "placeholder": "3600",
            }
        },
        {
            "LOGLEVEL": {
                "required": False,
                "help_text": "Log level",
                "label": "Loglevel",
                "placeholder": "INFO",
            }
        },
        {
            "MAX_DB_WAIT_TIME": {
                "required": False,
                "help_text": "Maximum time to wait for database, in seconds",
                "label": "Max DB Wait Time",
                "placeholder": "300",
            }
        },
    ],
}

NETBOX_SUPERUSER_SETTINGS = ["SUPERUSER_NAME", "SUPERUSER_EMAIL", "SUPERUSER_PASSWORD"]
