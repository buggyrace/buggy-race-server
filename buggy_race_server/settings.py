# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL")
SECRET_KEY = env.str("SECRET_KEY")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", default=43200)
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = "simple"  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False

BUGGY_EDITOR_GITHUB_URL = env.str("BUGGY_EDITOR_GITHUB_URL")
BUGGY_RACE_SERVER_URL = env.str("BUGGY_RACE_SERVER_URL")
SERVER_PROJECT_PAGE_PATH = env.str("SERVER_PROJECT_PAGE_PATH")
GITHUB_PAGES_URL= env.str("GITHUB_PAGES_URL")
MOODLE_URL = env.str("MOODLE_URL")

PERMANENT_SESSION_LIFETIME = env.int("PERMANENT_SESSION_LIFETIME", default=60*60*24)

RACE_LEAGUE = env.str("RACE_LEAGUE", default="fy")