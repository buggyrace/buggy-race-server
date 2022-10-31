# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

Create a .env file (by copying env.example and editing it)
or load environment variables in your own way

This class gathers them and potentially modifies them
(e.g., env vars must be strings, but via this mechanism
you can wash or cast type (e.g., admin usernames as a list))

"""
from environs import Env
import re

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

class ConfigFromEnv():

    # make sure that every config variable used is being picked up here
    # (avoid reaching directly into the environment variable elsewhere)

    INSTITUTION_SHORT_NAME = env.str("INSTITUTION_SHORT_NAME", default="Acme")
    INSTITUTION_FULL_NAME = env.str("INSTITUTION_FULL_NAME", default="Acme School of Buggy Programming")
    INSTITUTION_HOME_URL = env.str("INSTITUTION_HOME_URL", default="https://acme.example.com/")

    PROJECT_CODE = env.str("PROJECT_CODE", default="buggy")
    PROJECT_SLUG = env.str("PROJECT_SLUG", default=_slug(PROJECT_CODE))

    FLASK_APP = env.str("FLASK_APP", default="autoapp.py")
    FLASK_ENV = env.str("FLASK_ENV", default="production")    
    FLASK_DEBUG = DEBUG = FLASK_ENV == "development"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL = env.str("DATABASE_URL")
    GUNICORN_WORKERS = env.int("GUNICORN_WORKERS", default=1)
    LOG_LEVEL = env.str("LOG_LEVEL", default="debug")
    SECRET_KEY = env.str("SECRET_KEY", default="not-so-secret")

    # In production, set to a higher number, like 31556926
    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", default=43200)
    BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)

    DEBUG_TB_ENABLED = DEBUG
    DEBUG_TB_INTERCEPT_REDIRECTS = env.bool("DEBUG_TB_INTERCEPT_REDIRECTS", default=False)

    # Can be "memcached", "redis", etc.
    CACHE_TYPE = env.str("CACHE_TYPE", default="simple")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = env.bool("BCRYPT_LOG_ROUNDS", default=False)
    
    FORCE_REDIRECT_HTTP_TO_HTTPS = env.bool("FORCE_REDIRECT_HTTP_TO_HTTPS", default=False)

    # ----------------------------------------------------------#
    # buggy-racing specific settings follow:                    #
    # ----------------------------------------------------------#

    BUGGY_EDITOR_GITHUB_URL = env.str("BUGGY_EDITOR_GITHUB_URL", default="#MISSING-GITHUB-URL").strip()
    BUGGY_EDITOR_REPO_NAME = env.str("BUGGY_EDITOR_REPO_NAME", default="#MISSING-REPO-NAME").strip()
    BUGGY_EDITOR_REPO_OWNER = env.str("BUGGY_EDITOR_REPO_OWNER", default="#MISSING-REPO-OWNER").strip()

    # Path and filename of the markdown file of issues relative to the
    # servers root path e.g. /buggy_race_server
    BUGGY_EDITOR_ISSUES_FILE = env.str("BUGGY_EDITOR_ISSUES_FILE", default="../project/issues.csv").strip()

    # URL to the published docs
    # (e.g., the GitHub pages URL of the docs/ directory of this repo)
    GITHUB_PAGES_URL = env.str("GITHUB_PAGES_URL", default="").strip()

    BUGGY_RACE_SERVER_URL = _remove_slashes(env.str("BUGGY_RACE_SERVER_URL", default="http://localhost:5000"))
    SERVER_PROJECT_PAGE_PATH = _force_slashes(env.str("BUGGY_RACE_SERVER_URL", default="/project/"))

    # note that the env settings are not explicitly passed into the config:
    # they exist as the NAME/URL/TEXT fields of the objects in
    # this SOCIAL_LINKS list:
    SOCIAL_LINKS = _extract_social_links()

    # registration only allowed with an auth code: (case insensitive)
    # if not set, registration is public, which probably isn't what you want
    reg_auth_code = env.str("REGISTRATION_AUTH_CODE", default="localauth").strip()
    REGISTRATION_AUTH_CODE = reg_auth_code if reg_auth_code else None
    HAS_AUTH_CODE = REGISTRATION_AUTH_CODE is not None

    # comma-separated list of users who have access to admin:
    # currently this is how we're acknowledging admin (not using the is_admin
    # setting in the user model: this was for pragmatic/monkey-patch reasons
    # and needs to be fixed!)
    # But for now, admin power is granted via env variable:
    ADMIN_USERNAMES = env.str("ADMIN_USERNAMES", default="").strip()
    ADMIN_USERNAMES_LIST = [user.strip() for user in ADMIN_USERNAMES.split(",")]

    DEFAULT_RACE_LEAGUE = env.str("DEFAULT_RACE_LEAGUE", default="races").strip()
    DEFAULT_RACE_COST_LIMIT = env.int("DEFAULT_RACE_COST_LIMIT", 200)
    DEFAULT_RACE_IS_VISIBLE = env.bool("DEFAULT_RACE_IS_VISIBLE", False)

    # A special id used to identify the app asking for access to a github acc.
    # Read more here: https://docs.github.com/en/developers/apps/authorizing-oauth-apps#web-application-flow
    GITHUB_CLIENT_ID = env.str("GITHUB_CLIENT_ID", default="")

    # Special secret used to authorize our application making requests for 
    # oauth access tokens
    GITHUB_CLIENT_SECRET = env.str("GITHUB_CLIENT_SECRET", default="").strip()

    # Supported announcement types:
    # roughly, xyz maps to "announcement-xyz" CSS class — but see layout.html)
    # If you add more here, make sure you've also added support for them first
    ANNOUNCEMENT_TYPES = ['info', 'warning', 'special']

    # these are loaded from the database on the first request and then effectively
    # cached in the config to avoid repeated hits on the database
    CURRENT_ANNOUNCEMENTS = None

    # this is an example announcement to populate the database with a demo
    # (only if there are no announcements already loaded)
    # Be careful with this: broken HTML here will cause problems!
    EXAMPLE_ANNOUNCEMENT = "<strong>BUGGY RACING IS CURRENTLY SUSPENDED</strong><br>pending the start of the new racing season"

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

    # note: explicit mapping between name of field/column and enable/disable
    #   Developers: see users/models.py to see this in use: it's a bit messy
    #   if these settings are changed _after_ any records have been created
    #   (but that is why this is not implemented in the database schema, which
    #   might be generated before these config settings have been fixed)
    _USERS_ADDITIONAL_FIELDNAMES_IS_ENABLED = {
        "email": USERS_HAVE_EMAIL,
        "org_username": USERS_HAVE_ORG_USERNAME,
        "first_name": USERS_HAVE_FIRST_NAME,
        "last_name": USERS_HAVE_LAST_NAME
    }
