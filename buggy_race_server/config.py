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

"""

from enum import Enum
from environs import Env
from random import randint
import re

class ConfigSettingNames(str, Enum):

    # TODO: might want to make these explicity somewhere:
    # Some config settings (specifically, Flask-related ones) are missing here
    # because they are only set by environment variables (e.g., the database URL).

    # prefix by _ are implied, so should not be set explicitly
    _USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED="_USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED"
    _USERS_ADDITIONAL_FIELDNAMES="_USERS_ADDITIONAL_FIELDNAMES"
    _ADMIN_USERNAMES_LIST="_ADMIN_USERNAMES_LIST"
    _CURRENT_ANNOUNCEMENTS="_CURRENT_ANNOUNCEMENTS"
    _SETUP_STATUS="_SETUP_STATUS"

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
    IS_PUBLIC_REGISTRATION_ALLOWED="IS_PUBLIC_REGISTRATION_ALLOWED"
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

class ConfigGroupNames(str, Enum):
    """ Config settings are in groups to make the setting form more manageable """
    AUTH = "auth"
    ORG = "org"
    GITHUB = "github"
    USERS = "users"
    RACES = "races"
    SERVER = "server"
    SOCIAL = "social"

class ConfigTypes(str, Enum):
    """ Explicit types of config settings (useful for validation, etc) """
    STRING = "str" # default TODO maybe ""?
    BOOLEAN = "bool"
    INT = "int"
    URL = "url"
    PASSWORD = "pass"

class ConfigSettings:

    # config settings prefixed with _ are not set by user
    # but rather are implied once the config is set

    GROUPS = {
      ConfigGroupNames.AUTH.name:(
        ConfigSettingNames.REGISTRATION_AUTH_CODE.name
      ),
      ConfigGroupNames.ORG.name: (
        ConfigSettingNames.INSTITUTION_FULL_NAME.name,
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name,
        ConfigSettingNames.INSTITUTION_HOME_URL.name,
        ConfigSettingNames.PROJECT_CODE.name,
        ConfigSettingNames.PROJECT_SLUG.name,
      ),
      ConfigGroupNames.GITHUB.name: (
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name,
        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name,
        ConfigSettingNames.GITHUB_PAGES_URL.name,
        ConfigSettingNames.GITHUB_CLIENT_ID.name,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name,
      ),
      ConfigGroupNames.USERS.name: (
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name,
        ConfigSettingNames.USERS_HAVE_EMAIL.name,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name,
      ),
      ConfigGroupNames.RACES.name: {
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name,
      },
      ConfigGroupNames.SERVER.name:{
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name,
        ConfigSettingNames.ADMIN_USERNAMES.name,
        ConfigSettingNames.SECRET_KEY.name,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name,
      },
      ConfigGroupNames.SOCIAL.name: {
        ConfigSettingNames.SOCIAL_LINKS.name,
      }
    }
    DEFAULTS = {
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: "ASBP",
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: "Acme School of Buggy Programming",
        ConfigSettingNames.INSTITUTION_HOME_URL.name: "https://acme.example.com/",
        ConfigSettingNames.PROJECT_CODE.name: "Buggy",
        ConfigSettingNames.PROJECT_SLUG.name: "",
        ConfigSettingNames.SECRET_KEY.name: f"{randint(10000, 99999)}-secret-{randint(10000, 99999)}",
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: 0,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  "https://github.com/buggyrace/buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: "buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: "buggyrace",
        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name: "buggyrace-issues.csv",
        ConfigSettingNames.GITHUB_PAGES_URL.name: "",
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: "http://localhost:8000",
        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name: "project",
        ConfigSettingNames.SOCIAL_LINKS.name: "",
        ConfigSettingNames.REGISTRATION_AUTH_CODE.name: "CHANGEME",
        ConfigSettingNames.ADMIN_USERNAMES.name: "",
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: "",
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: 200,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: 0,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: "",
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: "",
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: 0,
        ConfigSettingNames.USERS_HAVE_EMAIL.name: 0,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: 0,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: 0,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: 0,
        ConfigSettingNames._SETUP_STATUS.name: 1, # by default, we're setting up
    }

    TYPES = {
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_HOME_URL.name: ConfigTypes.URL,
        ConfigSettingNames.PROJECT_CODE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SLUG.name: ConfigTypes.STRING,
        ConfigSettingNames.SECRET_KEY.name: ConfigTypes.STRING,
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  ConfigTypes.URL,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_PAGES_URL.name: ConfigTypes.URL,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: ConfigTypes.URL,
        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_LINKS.name: ConfigTypes.STRING, # TODO
        ConfigSettingNames.REGISTRATION_AUTH_CODE.name: ConfigTypes.PASSWORD,
        ConfigSettingNames.ADMIN_USERNAMES.name: ConfigTypes.STRING,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: ConfigTypes.STRING,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: ConfigTypes.INT,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: ConfigTypes.STRING,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_EMAIL.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames._SETUP_STATUS.name: ConfigTypes.INT,
    }

    # this is the order of the setting groups that is
    # used during the (initial) setup: the _SETUP_STATUS
    # config is effectively the index-1 into this array:
    # when the setup is complete, _SETUP_STATUS is zero.
    SETUP_GROUPS = [
      ConfigGroupNames.AUTH,
      ConfigGroupNames.ORG,
      ConfigGroupNames.USERS,
      ConfigGroupNames.SERVER,
      ConfigGroupNames.RACES,
      ConfigGroupNames.SOCIAL,
      ConfigGroupNames.GITHUB
    ]

    DESCRIPTIONS = {
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name:
          """Short name or abbreviation for your institution, college,
          or school.""",
        
        ConfigSettingNames.INSTITUTION_FULL_NAME.name:
          """Full name for your institution, college, or school""",

        ConfigSettingNames.INSTITUTION_HOME_URL.name:
          """Full URL for the home page of your institution: used as a link
          on the racing server's home page.""",

        ConfigSettingNames.PROJECT_CODE.name:
          """If this project is known by a course or module code, use it
          (for example, when we ran it at Royal Holloway, it was CS1999);
          otherwise, "Buggy" works. An automatically slugified form of
          this is used in filenames, etc., but if you want to specify your
          own, set `PROJECT_SLUG` here too.""",

        ConfigSettingNames.PROJECT_SLUG.name:
          """This is how the `PROJECT_CODE` appears in filenames: you only
          need to set this if the automatic slug (lowercase, spaces-to-hyphens
          and so on) isn't acceptable to you.""",

        ConfigSettingNames.SECRET_KEY.name:
          """A secret used by the webserver in cookies, etc. This should be unique
          for your server: the default value was randomised on installation,
          but you can choose your own value if you prefer.""",

        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name:
          """Should the webserver itself force HTTPS? This setting might not
          be helpful if your hosting environment manages this for you (that is,
          can be counterproductive to tell the server to force it here).
          HTTPS is mandatory for GitHub's OAuth authentication, or if you're
          holding any personal information on students. This setting does not
          _implement_ HTTPS: it only forces redirection if the protocol the web
          server sees in incoming requests is (non-secure) HTTP.""",

        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:
          """URL to the 'buggy editor' code the students need to start
          the project. This is a public repo and unless you've forked
          it to make a custom one, you probably don't need to change
          this.""",

        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name:
          """This should match the name in the `BUGGY_EDITOR_GITHUB_URL`
          and is used in some of the GitHub API calls: if you haven't
          changed the repo URL then you won't need to change this.""",

        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name:
          """The `BUGGY_EDITOR_GITHUB_URL` is public and owned by `buggyrace`.
          You don't need to change this unless you've forked your own custom
          version of the repo.""",

        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name:
          """Name of the CSV file the server creates that describes the project
          tasks as GitHub issues. You probably don't need to change this.""",

        ConfigSettingNames.GITHUB_PAGES_URL.name:
          """Full URL to the project info pages if they are not being hosted
          on this server. Normally the project info pages *are* on the race
          server, so this should be empty.""",

        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name:
          """Full URL of this server.""",

        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name:
          """Path to the project information pages: see `GITHUB_PAGES_URL`:
          it's unlikely that you'll need to change this unless you've explictly
          changed the way project info is hosted.
          """,

        ConfigSettingNames.SOCIAL_LINKS.name:
          """Description""",

        ConfigSettingNames.REGISTRATION_AUTH_CODE.name:
          """The authorisation code is needed to make any changes to user data,
          including registering students. If `IS_PUBLIC_REGISTRATION_ALLOWED`
          is 'Yes' then anyone can register a single user (not recommended).""",

        ConfigSettingNames.ADMIN_USERNAMES.name:
          """Comma separated list of admin user names. You can nominate usernames
          here before they have been registered.""",

        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name:
          """Races are grouped by league, so if you're using that mechanism you
          can nominate the league that new races are in here. It's common to
          run the race server without using leagues, so if you're not sure,
          leave this blank.""",

        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name:
          """The default point cost threshhold for buggies: you can always
          override this when you create each race.""",

        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name:
          """Should a race be public as soon as you create it? If you choose
          No, you'll have to remember to publish races in order for students
          to see it.""",

        ConfigSettingNames.GITHUB_CLIENT_ID.name:
          """The GitHub client ID for the GitHub app that the server uses to
          fork the buggy editor repo into a student's own GitHub account.""",

        ConfigSettingNames.GITHUB_CLIENT_SECRET.name:
          """A string that exactly matches the client secret stored on the
          GitHub app that the server uses tofork the buggy editor repo into
          a student's own GitHub account.""",

        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name:
          """Should usernames (which are always lower case) be displayed using
          title case? For example, choose 'Yes' if the usernames you're using
          are really students' names. Login is always case insensitive, so this
          only affects how usernames are displayed, not what users need to
          type.""",

        ConfigSettingNames.USERS_HAVE_EMAIL.name:
          """Do users need email addresses? The server doesn't send emails so
          you don't need this field unless it's a useful way of identifying
          a student.""",

        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name:
          """Do users have a username or account that's specific to your
          institution? You might not need this, or you might already be using
          it as the username — in which case choose 'No'.
          """,

        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name:
          """Do users need to have a first name? You might be using each student's
          first name as the username, in which case you don't need this.""",

        ConfigSettingNames.USERS_HAVE_LAST_NAME.name:
          """Do users need to have a last name? If you can already identify your
          students from the other fields, you might not need this.""",

        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name:
          """Can users register themselves? If not, only an admin user who
          knows the `AUTH_CODE` can register new users. Normally, the
          staff running the buggy racing project will register users so
          public registration should not be enabled."""

    }

    def prettify(name, value):
      if ConfigSettings.TYPES.get(name) == "bool":
        return "No" if (value == "0" or not bool(value)) else "Yes"
      return value

    def set_config_value(app, name, value):
        str_value = str(value)
        type = ConfigSettings.TYPES[name]
        if type == ConfigTypes.BOOLEAN:
            value = str_value == "1"
        elif type == ConfigTypes.INT:
            if str_value.isdecimal():
                value = int(str_value)
        app.config[name] = value

    def infer_extra_settings(app):
        """ Generates extra/convenience config settings that are
        implied from config settings that are already set. """

        app.config[ConfigSettingNames._ADMIN_USERNAMES_LIST.name] = [
            user.strip() for user in app.config[ConfigSettingNames.ADMIN_USERNAMES.name].split(",")
        ]

        # note: explicit mapping between name of field/column and enable/disable
        #   Developers: see users/models.py to see this in use: it's a bit messy
        #   if these settings are changed _after_ any records have been created
        #   (but that is why this is not implemented in the database schema, which
        #   might be generated before these config settings have been fixed)
        app.config[ConfigSettingNames._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED.name] = {
            "email": app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name],
            "org_username": app.config[ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name],
            "first_name": app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name],
            "last_name": app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name]
        }

        # list of additional fieldnames (will be empty if there are none)
        #   This is a convenience for summarising user settings
        additional_names = []
        for name in app.config[ConfigSettingNames._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED.name]:
            if app.config[ConfigSettingNames._USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED][name]:
                additional_names.append(name)
        app.config[ConfigSettingNames._USERS_ADDITIONAL_FIELDNAMES.name] = additional_names


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

    # set up phase:
    # 0 - none (full access to settings)
    # 1 - force change of auth code if unchanged
    # 2 - get admin username and password
    # default here is None so existing setting (in db) or default is used
    _SETUP_STATUS = env.str(str(ConfigSettingNames._SETUP_STATUS), default=None)

    # some (not-buggy-race-specific) config _only_ comes from the ENV
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
    
    SECRET_KEY = ConfigSettings.DEFAULTS[ConfigSettingNames.SECRET_KEY.name]

    # note that the env settings are not explicitly passed into the config:
    # they exist as the NAME/URL/TEXT fields of the objects in
    # this SOCIAL_LINKS list:
    #- SOCIAL_LINKS = _extract_social_links()

    # registration only allowed with an auth code: (case insensitive)
    # if not set, registration is public, which probably isn't what you want
    #- reg_auth_code = env.str("REGISTRATION_AUTH_CODE", default="localauth").strip()
    #- REGISTRATION_AUTH_CODE = reg_auth_code if reg_auth_code else None

    # comma-separated list of users who have access to admin:
    # currently this is how we're acknowledging admin (not using the is_admin
    # setting in the user model: this was for pragmatic/monkey-patch reasons
    # and needs to be fixed!)
    # But for now, admin power is granted via env variable:
    #- ADMIN_USERNAMES = env.str("ADMIN_USERNAMES", default="").strip()

    # Supported announcement types:
    # roughly, xyz maps to "announcement-xyz" CSS class — but see layout.html)
    # If you add more here, make sure you've also added support for them first

    # these are loaded from the database on the first request and then effectively
    # cached in the config to avoid repeated hits on the database
    #- CURRENT_ANNOUNCEMENTS = None

    # should usernames be capitalised when displayed?
    # usernames are always considered lowercase, but (if they are
    # student's names) you can choose to display them in titlecase
    # (so Ada instead of ada)
    #- IS_PRETTY_USERNAME_TITLECASE = env.bool("IS_PRETTY_USERNAME_TITLECASE", False)

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
    #- USERS_HAVE_EMAIL = env.bool("USERS_HAVE_EMAIL", default=False)
    #- USERS_HAVE_ORG_USERNAME = env.bool("USERS_HAVE_ORG_USERNAME", default=False)
    #- USERS_HAVE_FIRST_NAME = env.bool("USERS_HAVE_FIRST_NAME", default=False)
    #- USERS_HAVE_LAST_NAME = env.bool("USERS_HAVE_LAST_NAME", default=False)
