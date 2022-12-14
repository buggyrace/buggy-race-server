# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

Create a .env file (by copying env.example and editing it)
or load environment variables in your own way

This class gathers them and potentially modifies them
(e.g., env vars must be strings, but via this mechanism
you can wash or cast type (e.g., admin usernames as a list))

When the app loads: needs a DB connection (ENV var or other config?)
but everything else from the settings in the database:
  stored as set of name-value pairs
  but
  accessed as an object here in config

  * why use database?
   - Because files on heroku are transient, but DB persists
   - maybe easier to ue same form mechanism through ORM?

"""

from environs import Env
import re
from random import randint

class ConfigSettings:

    # these are the NAMES of the config settings (not their values!)

    TYPE_STRING = "str" # default TODO maybe ""?
    TYPE_BOOLEAN = "bool"
    TYPE_INT = "int"
    TYPE_URL = "url"

    # config settings prefixed with _ are not set by user
    # but rather are implied once the config is set
    _USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED="_USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED"
    _USERS_ADDITIONAL_FIELDNAMES="_USERS_ADDITIONAL_FIELDNAMES"
    _HAS_AUTH_CODE="_HAS_AUTH_CODE"
    _ADMIN_USERNAMES_LIST="_ADMIN_USERNAMES_LIST"

    ADMIN_USERNAMES="ADMIN_USERNAMES"
    BUGGY_EDITOR_GITHUB_URL="BUGGY_EDITOR_GITHUB_URL"
    BUGGY_EDITOR_ISSUES_FILE="BUGGY_EDITOR_ISSUES_FILE"
    BUGGY_EDITOR_REPO_NAME="BUGGY_EDITOR_REPO_NAME"
    BUGGY_EDITOR_REPO_OWNER="BUGGY_EDITOR_REPO_OWNER"
    BUGGY_RACE_SERVER_URL="BUGGY_RACE_SERVER_URL"
    DEFAULT_RACE_COST_LIMIT="DEFAULT_RACE_COST_LIMIT"
    DEFAULT_RACE_IS_VISIBLE="DEFAULT_RACE_IS_VISIBLE"
    DEFAULT_RACE_LEAGUE="DEFAULT_RACE_LEAGUE"
    FORCE_REDIRECT_HTTP_TO_HTTPS="FORCE_REDIRECT_HTTP_TO_HTTPS"
    GITHUB_CLIENT_ID="GITHUB_CLIENT_ID"
    GITHUB_CLIENT_SECRET="GITHUB_CLIENT_SECRET"
    GITHUB_PAGES_URL="GITHUB_PAGES_URL"
    INSTITUTION_FULL_NAME="INSTITUTION_FULL_NAME"
    INSTITUTION_HOME_URL="INSTITUTION_HOME_URL"
    INSTITUTION_SHORT_NAME="INSTITUTION_SHORT_NAME"
    IS_PRETTY_USERNAME_TITLECASE="IS_PRETTY_USERNAME_TITLECASE"
    PROJECT_CODE="PROJECT_CODE"
    PROJECT_SLUG="PROJECT_SLUG"
    REGISTRATION_AUTH_CODE="REGISTRATION_AUTH_CODE"
    SECRET_KEY="SECRET_KEY"
    SERVER_PROJECT_PAGE_PATH="SERVER_PROJECT_PAGE_PATH"
    SOCIAL_LINKS="SOCIAL_LINKS"
    USERS_HAVE_EMAIL="USERS_HAVE_EMAIL"
    USERS_HAVE_FIRST_NAME="USERS_HAVE_FIRST_NAME"
    USERS_HAVE_LAST_NAME="USERS_HAVE_LAST_NAME"
    USERS_HAVE_ORG_USERNAME="USERS_HAVE_ORG_USERNAME"

    GROUPS = {
    #   "_auto": ( # these are not stored in the database
    #     _USERS_ADDITIONAL_FIELDNAMES,
    #     _USERS_ADDITIONAL_FIELDNAMES_ENABLED
    #   ),
      "org": (
        INSTITUTION_FULL_NAME,
        INSTITUTION_SHORT_NAME,
        INSTITUTION_HOME_URL,
        PROJECT_CODE,
        PROJECT_SLUG,
      ),
      "github": (
        BUGGY_EDITOR_GITHUB_URL,
        BUGGY_EDITOR_REPO_NAME,
        BUGGY_EDITOR_REPO_OWNER,
        BUGGY_EDITOR_ISSUES_FILE,
        GITHUB_PAGES_URL,
        GITHUB_CLIENT_ID,
        GITHUB_CLIENT_SECRET,
      ),
      "users": (
        IS_PRETTY_USERNAME_TITLECASE,
        USERS_HAVE_EMAIL,
        USERS_HAVE_ORG_USERNAME,
        USERS_HAVE_FIRST_NAME,
        USERS_HAVE_LAST_NAME,
      ),
      "races": {
        DEFAULT_RACE_LEAGUE,
        DEFAULT_RACE_COST_LIMIT,
        DEFAULT_RACE_IS_VISIBLE,
      },
      "server":{
        FORCE_REDIRECT_HTTP_TO_HTTPS,
        BUGGY_RACE_SERVER_URL,
        SERVER_PROJECT_PAGE_PATH,
        REGISTRATION_AUTH_CODE,
        ADMIN_USERNAMES,
        SECRET_KEY,
      },
      "social": {
        SOCIAL_LINKS,
      }
    }
    DEFAULTS = {
        INSTITUTION_SHORT_NAME: "ASBP",
        INSTITUTION_FULL_NAME: "Acme School of Buggy Programming",
        INSTITUTION_HOME_URL: "https://acme.example.com/",
        PROJECT_CODE: "Buggy",
        PROJECT_SLUG: "",
        SECRET_KEY: f"{randint(1000, 9999)}-secret-{randint(1000, 9999)}",
        FORCE_REDIRECT_HTTP_TO_HTTPS: "",
        BUGGY_EDITOR_GITHUB_URL:  "https://github.com/buggyrace/buggy-race-editor",
        BUGGY_EDITOR_REPO_NAME: "buggy-race-editor",
        BUGGY_EDITOR_REPO_OWNER: "buggyrace",
        BUGGY_EDITOR_ISSUES_FILE: "",
        GITHUB_PAGES_URL: "",
        BUGGY_RACE_SERVER_URL: "",
        SERVER_PROJECT_PAGE_PATH: "",
        SOCIAL_LINKS: "",
        REGISTRATION_AUTH_CODE: "CHANGEME",
        ADMIN_USERNAMES: "",
        DEFAULT_RACE_LEAGUE: "",
        DEFAULT_RACE_COST_LIMIT: 200,
        DEFAULT_RACE_IS_VISIBLE: 0,
        GITHUB_CLIENT_ID: "",
        GITHUB_CLIENT_SECRET: "",
        IS_PRETTY_USERNAME_TITLECASE: 0,
        USERS_HAVE_EMAIL: 0,
        USERS_HAVE_ORG_USERNAME: 0,
        USERS_HAVE_FIRST_NAME: 0,
        USERS_HAVE_LAST_NAME: 0,
    }

    TYPES = {
        INSTITUTION_SHORT_NAME: TYPE_STRING,
        INSTITUTION_FULL_NAME: TYPE_STRING,
        INSTITUTION_HOME_URL: TYPE_URL,
        PROJECT_CODE: TYPE_STRING,
        PROJECT_SLUG: TYPE_STRING,
        SECRET_KEY: TYPE_STRING,
        FORCE_REDIRECT_HTTP_TO_HTTPS: TYPE_BOOLEAN,
        BUGGY_EDITOR_GITHUB_URL:  TYPE_URL,
        BUGGY_EDITOR_REPO_NAME: TYPE_STRING,
        BUGGY_EDITOR_REPO_OWNER: TYPE_STRING,
        BUGGY_EDITOR_ISSUES_FILE: TYPE_STRING,
        GITHUB_PAGES_URL: TYPE_URL,
        BUGGY_RACE_SERVER_URL: TYPE_URL,
        SERVER_PROJECT_PAGE_PATH: TYPE_STRING,
        SOCIAL_LINKS: TYPE_STRING, # TODO
        REGISTRATION_AUTH_CODE: TYPE_STRING,
        ADMIN_USERNAMES: TYPE_STRING,
        DEFAULT_RACE_LEAGUE: TYPE_STRING,
        DEFAULT_RACE_COST_LIMIT: TYPE_INT,
        DEFAULT_RACE_IS_VISIBLE: TYPE_BOOLEAN,
        GITHUB_CLIENT_ID: TYPE_STRING,
        GITHUB_CLIENT_SECRET: TYPE_STRING,
        IS_PRETTY_USERNAME_TITLECASE: TYPE_BOOLEAN,
        USERS_HAVE_EMAIL: TYPE_BOOLEAN,
        USERS_HAVE_ORG_USERNAME: TYPE_BOOLEAN,
        USERS_HAVE_FIRST_NAME: TYPE_BOOLEAN,
        USERS_HAVE_LAST_NAME: TYPE_BOOLEAN,
    }

    DESCRIPTIONS = {
        INSTITUTION_SHORT_NAME:
          """Short name for your institution, college, or school.""",
        
        INSTITUTION_FULL_NAME:
          """Full name for your institution, college, or school""",

        INSTITUTION_HOME_URL:
          """Full URL for the home page of your institution: used as a link
          on the racing server's home page.""",

        PROJECT_CODE:
          """If this project is known by a course or module code, use it
          (for example, when we ran it at Royal Holloway, it was CS1999);
          otherwise, "buggy" works. An automatically slugified form of
          this is used in filenames, etc., but if you want to specify your
          own, set PROJECT_SLUG here too.""",

        PROJECT_SLUG:
          """This is how the `PROJECT_CODE` appears in filenames: you only
          need to set this is the automatic slug (lowercase, spaces-to-hyphens
          and so on) isn't acceptable to you.""",

        SECRET_KEY:
          """A secret used by the webserver.""",

        FORCE_REDIRECT_HTTP_TO_HTTPS:
          """Should the webserver itself force HTTPS? This setting might not
          helpful if your hosting environment manages this for you (that is,
          it may already be handling this for you in which case it can be
          counterproductive to tell the server to force it here). HTTPS is
          mandatory for GitHub's OAuth authentication, or if you're holding any
          personal information on students (e.g., if you're using that GitHub
          mechanism, or storing email adresses).""",

        BUGGY_EDITOR_GITHUB_URL:
          """URL to the 'buggy editor' code the students need to start
          the project. This is a public repo and unless you've forked
          it to make a custom one, you probably don't need to change
          this.""",

        BUGGY_EDITOR_REPO_NAME:
          """This should match the name in the `BUGGY_EDITOR_GITHUB_URL`
          and is used in some of the GitHub API calls: if you haven't
          changed the repo URL then you won't need to change this.""",

        BUGGY_EDITOR_REPO_OWNER:
          """The `BUGGY_EDITOR_GITHUB_URL` is public and owned by `buggyrace`.
          You don't need to change this unless you've forked your own custom
          version of the repo.""",

        BUGGY_EDITOR_ISSUES_FILE:
          """Description""",

        GITHUB_PAGES_URL:
          """Description""",

        BUGGY_RACE_SERVER_URL:
          """Description""",

        SERVER_PROJECT_PAGE_PATH:
          """Description""",

        SOCIAL_LINKS:
          """Description""",

        REGISTRATION_AUTH_CODE:
          """Description""",

        ADMIN_USERNAMES:
          """Description""",

        DEFAULT_RACE_LEAGUE:
          """Description""",

        DEFAULT_RACE_COST_LIMIT:
          """Description""",

        DEFAULT_RACE_IS_VISIBLE:
          """Description""",

        GITHUB_CLIENT_ID:
          """Description""",

        GITHUB_CLIENT_SECRET:
          """Description""",

        IS_PRETTY_USERNAME_TITLECASE:
          """Description""",

        USERS_HAVE_EMAIL:
          """Description""",

        USERS_HAVE_ORG_USERNAME:
          """Description""",

        USERS_HAVE_FIRST_NAME:
          """Description""",

        USERS_HAVE_LAST_NAME:
          """Description""",

    }

    def set_config_value(app, name, value):
        str_value = str(value)
        type = ConfigSettings.TYPES[name]
        if type == ConfigSettings.TYPE_BOOLEAN:
            value = str_value == "1"
        elif type == ConfigSettings.TYPE_INT:
            if str_value.isdecimal():
                value = int(str_value)
        print(f"FIXME setting {name}: <{value}>", flush=True)
        app.config[name] = value

    def imply_extra_settings(app):
        """ Generates extra/convenience config settings that are
        implied from config settings that are already set. """

        app.config[ConfigSettings._HAS_AUTH_CODE] = app.config[ConfigSettings.REGISTRATION_AUTH_CODE] is not None
        app.config[ConfigSettings._ADMIN_USERNAMES_LIST] = [
            user.strip() for user in app.config[ConfigSettings.ADMIN_USERNAMES].split(",")
        ]

        # note: explicit mapping between name of field/column and enable/disable
        #   Developers: see users/models.py to see this in use: it's a bit messy
        #   if these settings are changed _after_ any records have been created
        #   (but that is why this is not implemented in the database schema, which
        #   might be generated before these config settings have been fixed)
        app.config[ConfigSettings._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED] = {
            "email": app.config[ConfigSettings.USERS_HAVE_EMAIL],
            "org_username": app.config[ConfigSettings.USERS_HAVE_ORG_USERNAME],
            "first_name": app.config[ConfigSettings.USERS_HAVE_FIRST_NAME],
            "last_name": app.config[ConfigSettings.USERS_HAVE_LAST_NAME]
        }

        # list of additional fieldnames (will be empty if there are none)
        #   This is a convenience for summarising user settings
        additional_names = []
        for name in app.config[ConfigSettings._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED]:
            if app.config[ConfigSettings._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED][name]:
                additional_names.append(name)
        app.config[ConfigSettings._USERS_ADDITIONAL_FIELDNAMES] = additional_names


env = Env()
env.read_env()

def _force_slashes(s):
    s = s.strip()
    if not s.startswith("/"):
        s = "/" + s
    if not s.endswith("/"):
        s = s + "/"
    return s

def _remove_slashes(s):
    s = s.strip()
    if s.startswith("/"):
       s = s[1:]
    if s.endswith("/"):
       s = s[:-1]
    return s

def _slug(s):
    return re.sub(r'\W+', '-', s.lower().strip())

# first social link is SOCIAL_NAME, SOCIAL_URL, SOCIAL_TEXT
# ...subsequent ones are SOCIAL_1_NAME, SOCIAL_1_URL, SOCIAL_1_TEXT
# and then 2 and 3 and...
def _extract_social_links():
    social_links = []
    if env.str("SOCIAL_URL", default="").strip():
        social_links.append({
          'NAME': env.str(f"SOCIAL_NAME", default=""),
          'URL':  env.str(f"SOCIAL_URL", default="").strip(),
          'TEXT': env.str(f"SOCIAL_TEXT", default="")
        })
    i = 1
    while env.str(f"SOCIAL_{i}_URL", default="").strip() != "":
        social_links.append({
          'NAME': env.str(f"SOCIAL_{i}_NAME", default=""),
          'URL':  env.str(f"SOCIAL_{i}_URL", default="").strip(),
          'TEXT': env.str(f"SOCIAL_{i}_TEXT", default="")
        })
        i += 1
    return social_links


##################################################################

class ConfigFromEnv():

    FLASK_APP = env.str("FLASK_APP", default="autoapp.py")
    FLASK_ENV = env.str("FLASK_ENV", default="production")
    FLASK_DEBUG = DEBUG = FLASK_ENV == "development"

    LOG_LEVEL = env.str("LOG_LEVEL", default="debug")
    BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
    DEBUG_TB_ENABLED = DEBUG
    DEBUG_TB_INTERCEPT_REDIRECTS = env.bool("DEBUG_TB_INTERCEPT_REDIRECTS", default=False)
    CACHE_TYPE = env.str("CACHE_TYPE", default="simple") # Can be "memcached", "redis", etc.

    SQLALCHEMY_TRACK_MODIFICATIONS = env.bool("BCRYPT_LOG_ROUNDS", default=False)

    # In production, set to a higher number, like 31556926
    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", default=43200)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL = env.str("DATABASE_URL")
    GUNICORN_WORKERS = env.int("GUNICORN_WORKERS", default=1)
    
    # note that the env settings are not explicitly passed into the config:
    # they exist as the NAME/URL/TEXT fields of the objects in
    # this SOCIAL_LINKS list:
    SOCIAL_LINKS = _extract_social_links()

    # registration only allowed with an auth code: (case insensitive)
    # if not set, registration is public, which probably isn't what you want
    reg_auth_code = env.str("REGISTRATION_AUTH_CODE", default="localauth").strip()
    REGISTRATION_AUTH_CODE = reg_auth_code if reg_auth_code else None

    # comma-separated list of users who have access to admin:
    # currently this is how we're acknowledging admin (not using the is_admin
    # setting in the user model: this was for pragmatic/monkey-patch reasons
    # and needs to be fixed!)
    # But for now, admin power is granted via env variable:
    ADMIN_USERNAMES = env.str("ADMIN_USERNAMES", default="").strip()

    # Supported announcement types:
    # roughly, xyz maps to "announcement-xyz" CSS class — but see layout.html)
    # If you add more here, make sure you've also added support for them first
    ANNOUNCEMENT_TYPES = ['info', 'warning', 'special']

    # these are loaded from the database on the first request and then effectively
    # cached in the config to avoid repeated hits on the database
    CURRENT_ANNOUNCEMENTS = None

    # should usernames be capitalised when displayed?
    # usernames are always considered lowercase, but (if they are
    # student's names) you can choose to display them in titlecase
    # (so Ada instead of ada)
    IS_PRETTY_USERNAME_TITLECASE = env.bool("IS_PRETTY_USERNAME_TITLECASE", False)

    # control which user fields are needed:
    # users always have a username...
    # ...but if you don't need the other fields, disable them
    # If you're running a small class, username might already be first name, so you
    # don't need to store other names.
    # Note:
    #   - the database still has all the columns, but their values won't
    #     be enforced
    #   - be aware of privacy issues (in general, and between other students)
    #     when setting these. The server may also storing (but not publishing)
    #     GitHub account information so even if you are disabling all of these
    #     you are still resonsible for securely and responsibly handling
    #     private data.
    USERS_HAVE_EMAIL = env.bool("USERS_HAVE_EMAIL", default=False)
    USERS_HAVE_ORG_USERNAME = env.bool("USERS_HAVE_ORG_USERNAME", default=False)
    USERS_HAVE_FIRST_NAME = env.bool("USERS_HAVE_FIRST_NAME", default=False)
    USERS_HAVE_LAST_NAME = env.bool("USERS_HAVE_LAST_NAME", default=False)
