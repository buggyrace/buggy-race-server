# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

Create a .env file (by copying env.example and editing it)
or load environment variables in your own way

This class gathers them and potentially modifies them
(e.g., env vars must be strings, but via this mechanism
you can wash or cast type (e.g., numeric))

"""
from environs import Env

env = Env()
env.read_env()

class Config(object):
    TESTING = False

def force_slashes(s):
    s = s.strip()
    if not s.startswith("/"):
        s = "/" + s
    if not s.endswith("/"):
        s= s + "/"
    return s

def remove_slashes(s):
    s = s.strip()
    if s.startswith("/"):
       s = s[1:]
    if s.endswith("/"):
       s = s[:-1]
    return s

class FromEnvConfig(Config):
  
    FLASK_APP = env.str("FLASK_APP", default="autoapp.py")
    FLASK_ENV = env.str("FLASK_ENV", default="production")    
    FLASK_DEBUG = DEBUG = FLASK_ENV == "development"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL = env.str("DATABASE_URL")
    GUNICORN_WORKERS = env.int("GUNICORN_WORKERS", default=1)
    LOG_LEVEL = env.str("LOG_LEVEL", default="debug")
    SECRET_KEY= env.str("SECRET_KEY", default="not-so-secret")

    # In production, set to a higher number, like 31556926
    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", default=43200)
    BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)

    DEBUG_TB_ENABLED = DEBUG
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    CACHE_TYPE = env.str("CACHE_TYPE", default="simple")  # Can be "memcached", "redis", etc.

    SQLALCHEMY_TRACK_MODIFICATIONS = env.bool("BCRYPT_LOG_ROUNDS", default=False)
    
    # ----------------------------------------------------------#
    # buggy-racing specific settings follow:                    #
    # ----------------------------------------------------------#

    BUGGY_EDITOR_GITHUB_URL = env.str("BUGGY_EDITOR_GITHUB_URL", default="").strip()
    BUGGY_EDITOR_REPO_NAME = env.str("BUGGY_EDITOR_REPO_NAME", default="").strip()
    BUGGY_EDITOR_REPO_OWNER = env.str("BUGGY_EDITOR_REPO_OWNER", default="").strip()

    # Path and filename of the markdown file of issues relative to the
    # servers root path e.g. /buggy_race_server
    BUGGY_EDITOR_ISSUES_FILE= env.str("BUGGY_EDITOR_ISSUES_FILE", default="../project/issues.csv").strip()

    # URL to the Piazza for Q&A discussion
    PIAZZA_URL= env.str("PIAZZA_URL", default="").strip()

    # URL to the published docs
    # (e.g., the GitHub pages URL of the docs/ directory of this repo)
    GITHUB_PAGES_URL=env.str("GITHUB_PAGES_URL", default="").strip()

    BUGGY_RACE_SERVER_URL=remove_slashes(env.str("BUGGY_RACE_SERVER_URL", default="http://localhost:5000"))
    SERVER_PROJECT_PAGE_PATH=force_slashes(env.str("BUGGY_RACE_SERVER_URL", default="/project/"))

    # URL to the course page for the project course
    #
    MOODLE_URL=env.str("MOODLE_URL", default="").strip()

    # registration only allowed with an auth code: (case insensitive)
    # if not set, registration is public, which probably isn't what you want
    #
    REGISTRATION_AUTH_CODE=env.str("REGISTRATION_AUTH_CODE", default="localauth").strip()

    # comma-separated list of users who have access to admin:
    # currently this is how we're acknowledging admin (not using the is_admin
    # setting in the user model: this was for pragmatic/monkey-patch reasons
    # and needs to be fixed!)
    # But for now, admin power is granted via env variable:
    #
    ADMIN_USERNNAMES=env.str("ADMIN_USERNNAMES", default="").strip()

    # A special id used to identify the app asking for access to a github acc.
    # Read more here: https://docs.github.com/en/developers/apps/authorizing-oauth-apps#web-application-flow
    GITHUB_CLIENT_ID=env.str("GITHUB_CLIENT_ID", default="")

    # Sepcial secret used to authorize our application making requests for 
    # oauth access tokens
    GITHUB_CLIENT_SECRET=env.str("GITHUB_CLIENT_SECRET", default="").strip()

    RACE_LEAGUE = env.str("RACE_LEAGUE", default="races").strip()
