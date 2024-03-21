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

from enum import Enum, auto
from environs import Env
from random import randint
from os import path
import re
from buggy_race_server.extensions import bcrypt

import pytz # timezones
from time import time

# ----------------------------------------------------------------------------
#  When you do a release, [try to remember to] bump the release details here!
# ----------------------------------------------------------------------------
#
MANUAL_LATEST_VERSION_IN_SOURCE = "v2.0.41"
#
# ----------------------------------------------------------------------------

# If you update the files in editor_source, update this to record which commit
# (presumably on main branch) of the repo it was from (you need to track this
# manually because we're _not_ using Git submodules)
# This is from https://github.com/buggyrace/buggy-race-editor/
#
MANUAL_EDITOR_COMMIT = "b8c9bc7fa90bcc34074b5b5b800878fca9c5d697"
#
# ----------------------------------------------------------------------------

class ConfigSettingNames(Enum):

    def _generate_next_value_(name, start, count, last_values):
        """ ConfigSettingNames values are the same (as strings) as their names."""
        return name

    #   These are the buggy-racing-specific config settings (that persist
    #   in the datbase(.)
    #   Some config settings (specifically, Flask-related ones) are missing
    #   here because they are only set by environment variables
    #   (e.g., the database URL or FLASK_APP) - see ConfigFromEnv, below,
    #   to see some of those settings. Those do not persist in the database.


    # Settings prefixed by _ are implied/managed entirely in code, so should
    # not be set by user (so: are not edited (or seen) in admin/settings

    # The commit hash for the snapshot of the editor files in this repo
    # (see note re: MANUAL_EDITOR_COMMIT above, which this is set to)
    _BUGGY_EDITOR_SOURCE_COMMIT = auto()

    # The URL of the buggyrace github repo for the editor — note this is the
    # one we use, not the forked one that the admins may be using — used to
    # link to the source from which the editor files included in this server
    # repo originated.
    _BUGGY_EDITOR_ORIGIN_GITHUB_URL = auto()

    # The name of the main python file (app.py) in the origin repo that
    # contains the (harcoded) race server URL
    _EDITOR_PYTHON_FILENAME = auto()

    # Name of the CSV file into which tasks-as-issues (for GitHub) are put
    _BUGGY_EDITOR_ISSUES_FILE = auto()

    # Current announcements are cached to avoid database reads on every hit
    _CURRENT_ANNOUNCEMENTS = auto()

    # Path where published HTML (task list and tech notes) and zip is written
    _PUBLISHED_PATH = auto()

    # Directory containing editor code (this itself contains a directory
    # that contains the files to be zipped: _EDITOR_REPO_DIR_NAME
    _EDITOR_INPUT_DIR = auto()
  
    # Directory, within published path, where buggy editor output is written
    # before (and after) zipping it up
    _EDITOR_OUTPUT_DIR = auto()

    # Name of directory that contains the actual files (contents from repo)
    # of the buggy editor — used as a container dir in both the source and
    # the output directory paths
    _EDITOR_REPO_DIR_NAME = auto()

    # The README in the buggy editor should be customised: this is the name
    # of the README file in the repo (it's a markdown file)
    _EDITOR_README_FILENAME = auto()

    # Path where static race assets (race player, etc) are found
    _RACE_ASSETS_PATH = auto()

    # Path where static racetrack assets (background images and path SVGs)
    # are found — might be a subdir of _RACE_ASSETS_PATH, but doesn't have
    # to be so, this is an entirely separate path
    _RACE_ASSETS_RACETRACK_PATH = auto()

    # dir where the default tasks are found, and the file name within it
    _PROJECT_TASKS_DIR_NAME = auto()
    _PROJECT_TASKS_FILENAME = auto()

    # Setup status is used to track progress (and ultimately completion)
    # of the setup process when the app is first installed
    _SETUP_STATUS = auto()

    # Timestamps that user never sets explicitly, but are stored as config
    _TASK_LIST_GENERATED_DATETIME = auto()
    _TASKS_LOADED_DATETIME = auto()
    _TECH_NOTES_GENERATED_DATETIME = auto()
    _EDITOR_ZIP_GENERATED_DATETIME = auto()

    # Filename of the generated task list (effectively static content)
    _TASK_LIST_HTML_FILENAME = auto()

    # Tech notes are managed by Pelcian: we don't anticipate the tech notes
    # dir being changed (it's in version control) but  putting them in config
    # to allow future tech notes to come from a different source
    _TECH_NOTES_CONFIG_FILE_NAME = auto()
    _TECH_NOTES_CONFIG_LIVE_NAME = auto()
    _TECH_NOTES_CONFIG_PATH = auto()
    _TECH_NOTES_CONFIG_PUBLISH_NAME = auto()
    _TECH_NOTES_CONTENT_DIR = auto()
    _TECH_NOTES_OUTPUT_DIR = auto()
    _TECH_NOTES_PAGES_DIR = auto()
    _TECH_NOTES_PATH = auto()

    # set to MANUAL_LATEST_VERSION_IN_SOURCE in the init method (see below)
    _VERSION_IN_SOURCE = auto()

    # if this is a (the?) demo server, set this true
    # This isn't being offered as an admin/web setting because it's really
    # only for buggyrace.net nerds and don't want to encourage confusion
    # with people trying to run a real server
    _IS_DEMO_SERVER = auto()

    # URL to the documentation for the buggy race project — specifically
    # the default is (risky?) linking to the /docs path within it
    # This is not exposed in the admin interface because (unlike the
    # student-facing texts like tech notes and tasks), we don't
    # anticipate the server docs being customised.
    _BUGGY_RACE_DOCS_URL = auto()

    # User-editable config settings: presented in the settings/config.
    # Each one should also exist in a settings group, and have a description
    # and a type.
    USER_ACTVITY_PERIOD_S = auto()
    AUTHORISATION_CODE = auto()
    BUGGY_EDITOR_GITHUB_URL = auto()
    BUGGY_EDITOR_REPO_NAME = auto()
    BUGGY_EDITOR_REPO_OWNER = auto()
    BUGGY_EDITOR_DOWNLOAD_URL = auto()
    BUGGY_EDITOR_ZIPFILE_NAME = auto()
    BUGGY_RACE_PLAYER_ANCHOR = auto()
    BUGGY_RACE_PLAYER_URL = auto()
    BUGGY_RACE_SERVER_TIMEZONE = auto()
    BUGGY_RACE_SERVER_URL = auto()
    API_SECRET_TIME_TO_LIVE = auto()
    DEFAULT_RACE_COST_LIMIT = auto()
    DEFAULT_RACE_LEAGUE = auto()
    EXT_ID_NAME = auto()
    EXT_ID_EXAMPLE = auto()
    EXT_USERNAME_EXAMPLE = auto()
    EXT_USERNAME_NAME = auto()
    GITHUB_CLIENT_ID = auto()
    GITHUB_CLIENT_SECRET = auto()
    INSTITUTION_FULL_NAME = auto()
    INSTITUTION_HOME_URL = auto()
    INSTITUTION_SHORT_NAME = auto()
    IS_ALL_CONFIG_IN_TECH_NOTES = auto()
    IS_API_SECRET_ONE_TIME_PW = auto()
    IS_BUGGY_DELETE_ALLOWED = auto()
    IS_DNF_POSITION_DEFAULT = auto()
    IS_WRITING_SERVER_URL_IN_EDITOR = auto()
    IS_FAKE_LATEX_CHOICE_ENABLED = auto()
    IS_ISSUES_CSV_CRLF_TERMINATED = auto()
    IS_PRETTY_USERNAME_TITLECASE = auto()
    IS_PROJECT_ZIP_INFO_DISPLAYED = auto()
    IS_PUBLIC_REGISTRATION_ALLOWED = auto()
    IS_RACE_FILE_DATE_STAMPED = auto()
    IS_RACE_FILE_START_STAMPED = auto()
    IS_RACE_VISIBLE_BY_DEFAULT = auto()
    IS_REDIRECT_HTTP_TO_HTTPS_FORCED = auto()
    IS_SHOWING_EXAMPLE_RACETRACKS = auto()
    IS_SHOWING_PROJECT_WORKFLOW = auto()
    IS_SHOWING_RESTART_SUGGESTION = auto()
    IS_STATIC_CONTENT_AUTOGENERATED = auto()
    IS_STORING_RACE_FILES_IN_DB = auto()
    IS_STORING_STUDENT_TASK_TEXTS = auto()
    IS_STUDENT_API_OTP_ALLOWED = auto()
    IS_STUDENT_USING_GITHUB_REPO = auto()
    IS_TA_EDIT_COMMENT_ENABLED = auto()
    IS_TA_PASSWORD_CHANGE_ENABLED = auto()
    IS_TASK_URL_WITH_ANCHOR = auto()
    IS_TECH_NOTE_PUBLISHING_ENABLED = auto()
    IS_USERNAME_PUBLIC_IN_RESULTS = auto()
    IS_USING_GITHUB = auto()
    IS_USING_GITHUB_API_TO_FORK = auto()
    IS_USING_GITHUB_API_TO_INJECT_ISSUES = auto()
    IS_USING_REMOTE_VS_WORKSPACE = auto()
    PROJECT_CODE = auto()
    PROJECT_PHASE_MIN_TARGET = auto()
    PROJECT_REMOTE_SERVER_ADDRESS = auto()
    PROJECT_REMOTE_SERVER_APP_URL = auto()
    PROJECT_REMOTE_SERVER_NAME = auto()
    PROJECT_REPORT_TYPE = auto()
    PROJECT_SLUG = auto()
    PROJECT_SUBMISSION_DEADLINE = auto()
    PROJECT_SUBMISSION_LINK = auto()
    PROJECT_WORKFLOW_URL = auto()
    PROJECT_ZIP_NAME_TYPE = auto()
    SECRET_KEY = auto()
    SOCIAL_0_NAME = auto()
    SOCIAL_0_TEXT = auto()
    SOCIAL_0_URL = auto()
    SOCIAL_1_NAME = auto()
    SOCIAL_1_TEXT = auto()
    SOCIAL_1_URL = auto()
    SOCIAL_2_NAME = auto()
    SOCIAL_2_TEXT = auto()
    SOCIAL_2_URL = auto()
    SOCIAL_3_NAME = auto()
    SOCIAL_3_TEXT = auto()
    SOCIAL_3_URL = auto()
    SUPERBASICS_URL = auto()
    TASK_NAME_FOR_API = auto()
    TASK_NAME_FOR_ENV_VARS = auto()
    TASK_NAME_FOR_GET_CODE = auto()
    TASK_NAME_FOR_VALIDATION = auto()
    TECH_NOTES_EXTERNAL_URL = auto()
    USERNAME_EXAMPLE = auto()
    USERS_HAVE_EMAIL = auto()
    USERS_HAVE_EXT_ID = auto()
    USERS_HAVE_EXT_USERNAME = auto()
    USERS_HAVE_FIRST_NAME = auto()
    USERS_HAVE_LAST_NAME = auto()

class ConfigGroupNames(str, Enum):
    """ Config settings are in groups to make the setting form more manageable """
    AUTH = "auth"
    GITHUB = "github"
    ORG = "org"
    PROJECT = "project"
    RACES = "races"
    SERVER = "server"
    SOCIAL = "social"
    TASKS = "tasks"
    TECH_NOTES = "tech_notes"
    USERS = "users"

class ConfigTypes(str, Enum):
    """ Explicit types of config settings (useful for validation, etc).
      A sensitive string is one that should be obscured by default on
      screens but — unlike a password — _is_ stored in plaintext. """
    BOOLEAN = "bool"
    DATETIME = "datetime"
    INT = "int"
    PASSWORD = "pass"
    SENSITIVE_STRING = "sensitive" # string, but obscured in display
    STRING = "str"
    TIMEZONE = "timezone"
    URL = "url"

class ConfigSettings:

    # Config settings prefixed with _ are not set by user, so do not appear
    # in GROUPS, which are used to present related settings together in the
    # admin/settings pages (otherwise it's overwhelming to manage).
    # If a setting isn't in a group here, the admin cannot change it through
    # the (web) admin/settings interface, but can still set it in the ENV
    # (or potentially in the database).

    # Deliberately excluded from GROUPS:
    #    ConfigSettingNames.SECRET_KEY
    #    because most users unlikely to ever need this and it breaks
    #    the session you're changing it in.

    GROUPS = {
      ConfigGroupNames.AUTH.name:(
        ConfigSettingNames.AUTHORISATION_CODE.name
      ),
      ConfigGroupNames.ORG.name: (
        ConfigSettingNames.INSTITUTION_FULL_NAME.name,
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name,
        ConfigSettingNames.INSTITUTION_HOME_URL.name,
      ),
      ConfigGroupNames.GITHUB.name: (
        ConfigSettingNames.IS_USING_GITHUB.name,
        ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name,
        ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name,
        ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name,
        ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name,
        ConfigSettingNames.GITHUB_CLIENT_ID.name,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name,
      ),
      ConfigGroupNames.USERS.name: (
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name,
        ConfigSettingNames.USERS_HAVE_EMAIL.name,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name,
        ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name,
        ConfigSettingNames.USERS_HAVE_EXT_ID.name,
        ConfigSettingNames.USERNAME_EXAMPLE.name,
        ConfigSettingNames.EXT_USERNAME_NAME.name,
        ConfigSettingNames.EXT_USERNAME_EXAMPLE.name,
        ConfigSettingNames.EXT_ID_NAME.name,
        ConfigSettingNames.EXT_ID_EXAMPLE.name,
        ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name,
        ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name,
        ConfigSettingNames.USER_ACTVITY_PERIOD_S.name,
      ),
      ConfigGroupNames.RACES.name: (
        ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name,
        # ConfigSettingNames.DEFAULT_RACE_LEAGUE.name, # not implemented yet
        ConfigSettingNames.IS_SHOWING_EXAMPLE_RACETRACKS.name,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name,
        ConfigSettingNames.IS_DNF_POSITION_DEFAULT.name,
        ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name,
        ConfigSettingNames.BUGGY_RACE_PLAYER_URL.name,
        ConfigSettingNames.BUGGY_RACE_PLAYER_ANCHOR.name,
        ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name,
        ConfigSettingNames.IS_RACE_FILE_START_STAMPED.name,
        ConfigSettingNames.IS_RACE_FILE_DATE_STAMPED.name,
      ),
      ConfigGroupNames.SERVER.name: (
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
        ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name,
        ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name,
        ConfigSettingNames.IS_REDIRECT_HTTP_TO_HTTPS_FORCED.name,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name,
        ConfigSettingNames.IS_BUGGY_DELETE_ALLOWED.name,
        ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name,
        ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name,
        ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name,
        ConfigSettingNames.IS_SHOWING_RESTART_SUGGESTION.name,
      ),
      ConfigGroupNames.SOCIAL.name: (
        ConfigSettingNames.SOCIAL_0_NAME.name,
        ConfigSettingNames.SOCIAL_0_TEXT.name,
        ConfigSettingNames.SOCIAL_0_URL.name,
        ConfigSettingNames.SOCIAL_1_NAME.name,
        ConfigSettingNames.SOCIAL_1_TEXT.name,
        ConfigSettingNames.SOCIAL_1_URL.name,
        ConfigSettingNames.SOCIAL_2_NAME.name,
        ConfigSettingNames.SOCIAL_2_TEXT.name,
        ConfigSettingNames.SOCIAL_2_URL.name,
        ConfigSettingNames.SOCIAL_3_NAME.name,
        ConfigSettingNames.SOCIAL_3_TEXT.name,
        ConfigSettingNames.SOCIAL_3_URL.name,
      ),
      ConfigGroupNames.PROJECT.name: (
        ConfigSettingNames.PROJECT_REPORT_TYPE.name,
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name,
        ConfigSettingNames.PROJECT_CODE.name,
        ConfigSettingNames.PROJECT_SLUG.name,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name,
        ConfigSettingNames.PROJECT_ZIP_NAME_TYPE.name,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_APP_URL.name,
        ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name,
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name,
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name,
        ConfigSettingNames.SUPERBASICS_URL.name,
      ),
      ConfigGroupNames.TASKS.name: (
        ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name,
        ConfigSettingNames.TASK_NAME_FOR_VALIDATION.name,
        ConfigSettingNames.TASK_NAME_FOR_GET_CODE.name,
        ConfigSettingNames.TASK_NAME_FOR_ENV_VARS.name,
        ConfigSettingNames.TASK_NAME_FOR_API.name,
        ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name,
        ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name,
      ),  
      ConfigGroupNames.TECH_NOTES.name: (
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name,
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name,
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name,
        ConfigSettingNames.IS_FAKE_LATEX_CHOICE_ENABLED.name,
      )
    }

    # **Every** config setting in ConfigSettingNames **must** have an entry
    # in the DEFAULTS (it's used during setup to populate the database)

    DEFAULTS = {
        ConfigSettingNames._BUGGY_EDITOR_SOURCE_COMMIT.name: MANUAL_EDITOR_COMMIT,
        ConfigSettingNames._BUGGY_EDITOR_ORIGIN_GITHUB_URL.name: "https://github.com/buggyrace/buggy-race-editor",
        ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name: "buggy-editor-issues.csv",
        ConfigSettingNames._BUGGY_RACE_DOCS_URL.name: "https://www.buggyrace.net/docs",
        ConfigSettingNames._EDITOR_PYTHON_FILENAME.name: "app.py",
        ConfigSettingNames._EDITOR_INPUT_DIR.name: "editor_source",
        ConfigSettingNames._EDITOR_OUTPUT_DIR.name: "editor",
        ConfigSettingNames._EDITOR_README_FILENAME.name: "README.md",
        ConfigSettingNames._EDITOR_REPO_DIR_NAME.name: "buggy-race-editor",
        ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name: "",
        ConfigSettingNames._IS_DEMO_SERVER.name: 0,
        ConfigSettingNames._PUBLISHED_PATH.name: "published",
        ConfigSettingNames._PROJECT_TASKS_DIR_NAME.name: "project",
        ConfigSettingNames._PROJECT_TASKS_FILENAME.name: "tasks.md",
        ConfigSettingNames._RACE_ASSETS_PATH.name: path.join("buggy_race_server", "race", "assets"),
        ConfigSettingNames._RACE_ASSETS_RACETRACK_PATH.name: path.join("buggy_race_server", "race", "assets", "tracks"),
        ConfigSettingNames._SETUP_STATUS.name: 1, # by default, we're setting up!
        ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name: "",
        ConfigSettingNames._TASK_LIST_HTML_FILENAME.name: "_task_list.html",
        ConfigSettingNames._TASKS_LOADED_DATETIME.name: "",
        ConfigSettingNames._TECH_NOTES_CONFIG_FILE_NAME.name: "pelicanconf.py",
        ConfigSettingNames._TECH_NOTES_CONFIG_LIVE_NAME.name: "pelicanconflive.py",
        ConfigSettingNames._TECH_NOTES_CONFIG_PUBLISH_NAME.name: "publishconf.py",
        ConfigSettingNames._TECH_NOTES_CONTENT_DIR.name: "content",
        ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name: "",
        ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name: "tech_notes",
        ConfigSettingNames._TECH_NOTES_PAGES_DIR.name: "pages",
        ConfigSettingNames._TECH_NOTES_PATH.name: "tech_notes",
        ConfigSettingNames.AUTHORISATION_CODE.name: bcrypt.generate_password_hash("CHANGEME").decode('utf8'),
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  "https://github.com/buggyrace/buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: "buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: "buggyrace",
        ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name: "buggy-race-editor.zip",
        ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name: "",
        ConfigSettingNames.BUGGY_RACE_PLAYER_ANCHOR.name: "#replay",
        ConfigSettingNames.BUGGY_RACE_PLAYER_URL.name: "",
        ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name: pytz.timezone("Europe/London"),
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: "http://localhost:8000",
        ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name: 60*60, # (in seconds) 1 hour
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: 200,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: "",
        ConfigSettingNames.EXT_ID_EXAMPLE.name: "12345",
        ConfigSettingNames.EXT_ID_NAME.name: "External ID",
        ConfigSettingNames.EXT_USERNAME_EXAMPLE.name: "abcd123",
        ConfigSettingNames.EXT_USERNAME_NAME.name: "Ext. username",
        ConfigSettingNames.GITHUB_CLIENT_ID.name: "",
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: "",
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: "Acme School of Buggy Programming",
        ConfigSettingNames.INSTITUTION_HOME_URL.name: "https://acme.example.com/",
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: "ASBP",
        ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name: 0,
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name: 1,
        ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name: 0,
        ConfigSettingNames.IS_BUGGY_DELETE_ALLOWED.name: 0,
        ConfigSettingNames.IS_DNF_POSITION_DEFAULT.name: 1,
        ConfigSettingNames.IS_FAKE_LATEX_CHOICE_ENABLED.name: 0,
        ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name: 0,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: 1,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: 1,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: 0,
        ConfigSettingNames.IS_RACE_FILE_DATE_STAMPED.name: 0,
        ConfigSettingNames.IS_RACE_FILE_START_STAMPED.name: 1,
        ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name: 0,
        ConfigSettingNames.IS_REDIRECT_HTTP_TO_HTTPS_FORCED.name: 0,
        ConfigSettingNames.IS_SHOWING_EXAMPLE_RACETRACKS.name: 1,
        ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name: 0,
        ConfigSettingNames.IS_SHOWING_RESTART_SUGGESTION.name: 0,
        ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name: 0,
        ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name: 1,
        ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name: 1,
        ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name: 1,
        ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name: 0,
        ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name: 1,
        ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name: 1,
        ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name: 0,
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name: 1,
        ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name: 1,
        ConfigSettingNames.IS_USING_GITHUB.name: 0,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name: 0,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name: 1,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name: 0,
        ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name: 1,
        ConfigSettingNames.PROJECT_CODE.name: "",
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name: 3,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name: "",
        ConfigSettingNames.PROJECT_REMOTE_SERVER_APP_URL.name: "",
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name: "",
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: "report",
        ConfigSettingNames.PROJECT_SLUG.name: "",
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: "",
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: "",
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name: "",
        ConfigSettingNames.PROJECT_ZIP_NAME_TYPE.name: "username",
        ConfigSettingNames.SECRET_KEY.name: f"{randint(10000, 99999)}-secret-{randint(10000, 99999)}",
        ConfigSettingNames.SOCIAL_0_NAME.name: "",
        ConfigSettingNames.SOCIAL_0_TEXT.name: "",
        ConfigSettingNames.SOCIAL_0_URL.name: "",
        ConfigSettingNames.SOCIAL_1_NAME.name: "",
        ConfigSettingNames.SOCIAL_1_TEXT.name: "",
        ConfigSettingNames.SOCIAL_1_URL.name: "",
        ConfigSettingNames.SOCIAL_2_NAME.name: "",
        ConfigSettingNames.SOCIAL_2_TEXT.name: "",
        ConfigSettingNames.SOCIAL_2_URL.name: "",
        ConfigSettingNames.SOCIAL_3_NAME.name: "",
        ConfigSettingNames.SOCIAL_3_TEXT.name: "",
        ConfigSettingNames.SOCIAL_3_URL.name: "",
        ConfigSettingNames.SUPERBASICS_URL.name: "https://superbasics.beholder.uk",
        ConfigSettingNames.TASK_NAME_FOR_GET_CODE.name: "0-GET",
        ConfigSettingNames.TASK_NAME_FOR_ENV_VARS.name: "3-ENV",
        ConfigSettingNames.TASK_NAME_FOR_API.name: "4-API",
        ConfigSettingNames.TASK_NAME_FOR_VALIDATION.name: "1-VALID",
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name: "",
        ConfigSettingNames.USER_ACTVITY_PERIOD_S.name: 60 * 5,
        ConfigSettingNames.USERNAME_EXAMPLE.name: "hamster",
        ConfigSettingNames.USERS_HAVE_EMAIL.name: 0,
        ConfigSettingNames.USERS_HAVE_EXT_ID.name: 0,
        ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name: 0,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: 0,

    }    
    
    MIN_PASSWORD_LENGTH = 4
    MIN_USERNAME_LENGTH = 2
    MAX_USERNAME_LENGTH = 32

    # TYPES are used to force casting when input either through the
    # admin/settings interface or simply when read as strings from ENV or the
    # database. By default they are strings, but it's best to be explicit.

    TYPES = {
        ConfigSettingNames._BUGGY_EDITOR_SOURCE_COMMIT.name: ConfigTypes.STRING,
        ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name: ConfigTypes.STRING,
        ConfigSettingNames._BUGGY_RACE_DOCS_URL.name: ConfigTypes.URL,
        ConfigSettingNames._EDITOR_PYTHON_FILENAME.name: ConfigTypes.STRING,
        ConfigSettingNames._EDITOR_INPUT_DIR.name: ConfigTypes.STRING,
        ConfigSettingNames._EDITOR_OUTPUT_DIR.name: ConfigTypes.STRING,
        ConfigSettingNames._EDITOR_README_FILENAME.name: ConfigTypes.STRING,
        ConfigSettingNames._EDITOR_REPO_DIR_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name: ConfigTypes.DATETIME,
        ConfigSettingNames._IS_DEMO_SERVER.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames._PUBLISHED_PATH.name: ConfigTypes.STRING,
        ConfigSettingNames._PROJECT_TASKS_DIR_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames._PROJECT_TASKS_FILENAME.name: ConfigTypes.STRING,
        ConfigSettingNames._SETUP_STATUS.name: ConfigTypes.INT,
        ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name: ConfigTypes.DATETIME,
        ConfigSettingNames._TASK_LIST_HTML_FILENAME.name: ConfigTypes.STRING,
        ConfigSettingNames._TASKS_LOADED_DATETIME.name: ConfigTypes.DATETIME,
        ConfigSettingNames._TECH_NOTES_CONFIG_FILE_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_CONFIG_LIVE_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_CONFIG_PUBLISH_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_CONTENT_DIR.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name: ConfigTypes.DATETIME,
        ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_PAGES_DIR.name: ConfigTypes.STRING,
        ConfigSettingNames._TECH_NOTES_PATH.name: ConfigTypes.STRING,
        ConfigSettingNames.AUTHORISATION_CODE.name: ConfigTypes.PASSWORD,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  ConfigTypes.URL,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name: ConfigTypes.URL,
        ConfigSettingNames.BUGGY_RACE_PLAYER_URL.name: ConfigTypes.URL,
        ConfigSettingNames.BUGGY_RACE_PLAYER_ANCHOR.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name: ConfigTypes.TIMEZONE,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: ConfigTypes.URL,
        ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name: ConfigTypes.INT,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: ConfigTypes.INT,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: ConfigTypes.STRING,
        ConfigSettingNames.EXT_ID_EXAMPLE.name: ConfigTypes.STRING,
        ConfigSettingNames.EXT_ID_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.EXT_USERNAME_EXAMPLE.name: ConfigTypes.STRING,
        ConfigSettingNames.EXT_USERNAME_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: ConfigTypes.SENSITIVE_STRING,
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_HOME_URL.name: ConfigTypes.URL,
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_BUGGY_DELETE_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_DNF_POSITION_DEFAULT.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_FAKE_LATEX_CHOICE_ENABLED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_RACE_FILE_DATE_STAMPED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_RACE_FILE_START_STAMPED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_REDIRECT_HTTP_TO_HTTPS_FORCED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_SHOWING_EXAMPLE_RACETRACKS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_SHOWING_RESTART_SUGGESTION.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USING_GITHUB.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.PROJECT_CODE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name: ConfigTypes.INT,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_APP_URL.name: ConfigTypes.URL,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SLUG.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: ConfigTypes.DATETIME,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: ConfigTypes.URL,
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_ZIP_NAME_TYPE.name: ConfigTypes.STRING,
        ConfigSettingNames.SECRET_KEY.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_0_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_0_TEXT.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_0_URL.name: ConfigTypes.URL,
        ConfigSettingNames.SOCIAL_1_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_1_TEXT.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_1_URL.name: ConfigTypes.URL,
        ConfigSettingNames.SOCIAL_2_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_2_TEXT.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_2_URL.name: ConfigTypes.URL,
        ConfigSettingNames.SOCIAL_3_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_3_TEXT.name: ConfigTypes.STRING,
        ConfigSettingNames.SOCIAL_3_URL.name: ConfigTypes.URL,
        ConfigSettingNames.SUPERBASICS_URL.name: ConfigTypes.URL,
        ConfigSettingNames.TASK_NAME_FOR_GET_CODE.name: ConfigTypes.STRING,
        ConfigSettingNames.TASK_NAME_FOR_ENV_VARS.name: ConfigTypes.STRING,
        ConfigSettingNames.TASK_NAME_FOR_API.name: ConfigTypes.STRING,
        ConfigSettingNames.TASK_NAME_FOR_VALIDATION.name: ConfigTypes.STRING,
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name: ConfigTypes.URL,
        ConfigSettingNames.USER_ACTVITY_PERIOD_S.name: ConfigTypes.INT,
        ConfigSettingNames.USERNAME_EXAMPLE.name: ConfigTypes.STRING,
        ConfigSettingNames.USERS_HAVE_EMAIL.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_EXT_ID.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: ConfigTypes.BOOLEAN,
    }

    # This is the order of the setting groups that is used during the
    # (initial) setup: the _SETUP_STATUS config is effectively the index-1
    # into this array: when the setup is complete, _SETUP_STATUS is zero.
    # (the settings page uses the same order, because it's sensible)
    SETUP_GROUPS = [
      ConfigGroupNames.AUTH.name,
      ConfigGroupNames.SERVER.name,
      ConfigGroupNames.ORG.name,
      ConfigGroupNames.SOCIAL.name,
      ConfigGroupNames.USERS.name,
      ConfigGroupNames.PROJECT.name,
      ConfigGroupNames.TASKS.name,
      ConfigGroupNames.TECH_NOTES.name,
      ConfigGroupNames.RACES.name,
      ConfigGroupNames.GITHUB.name
    ]

    DESCRIPTIONS = {

        ConfigSettingNames.AUTHORISATION_CODE.name:
          """The authorisation code is needed to make any changes to config or
          other-user data, including registering students. See also
          `IS_PUBLIC_REGISTRATION_ALLOWED` for an exception.""",

        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:
          """URL to the 'buggy editor' code the students need to start the
          project. This will usually be the URL to your customised, forked
          repo. If `IS_USING_GITHUB` is `No`, this setting is ignored.""",

        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name:
          """This should match the name in the `BUGGY_EDITOR_GITHUB_URL` and is
          used in some of the GitHub API calls: if you've forked the repo and
          not changed its name, you won't need to change this. If
          `IS_USING_GITHUB` is `No`, this setting is ignored.""",

        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name:
          """The `BUGGY_EDITOR_GITHUB_URL` is public and owned by `buggyrace`.
          If you've forked the repo (and customised it), change this to your
          GitHub username. It should match the username that appears in
          `BUGGY_EDITOR_GITHUB_URL`. If `IS_USING_GITHUB` is `No`, this setting
          is ignored.""",

        ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name:
          """If you are **not** using GitHub (`IS_USING_GITHUB` is `No`), and
          want to use the default buggy editor source code served from this
          server, what is the name of the zip file?""",

        ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name:
          """If you are **not** using GitHub (`IS_USING_GITHUB` is `No`), your
          students can download the buggy editor zipfile directly from this
          server. If you prefer to provide your own copy instead, provide a URL
          to your own instructions or zipfile instead. This setting is ignored
          if `IS_USING_GITHUB` is `Yes`. """,

        ConfigSettingNames.BUGGY_RACE_PLAYER_ANCHOR.name:
          """Anchor which is appended to any race player URLs. If the race
          player page has a header (which the default player on this server
          does), this scrolls that out of the way. If you don't prefix this
          with `#`, it will automatically be added.""",

        ConfigSettingNames.BUGGY_RACE_PLAYER_URL.name:
        """If you want to override the default race player and host your own,
        specify it here and races will link to that instead (passing the
        'results file' URL as a query variable called `race`). Do this if you
        want or need to run this as a standalone service (e.g., hosted on
        GitHubPages and potentially totally customised). If you don't specify a
        URL, races will use the race player on this server.""",

        ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name:
        """The timezone the race server is running in (that's almost certainly
        the timezone you or your classes are in). In the database, all
        timezones are stored in UTC, but should be converted to this on the way
        between the server and your (and your students') screens. If this is an
        invalid timezone (according to Python), it will revert to UTC.""",

        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name:
          """Full ("base") URL of this server (do not include a trailing
          slash).""",

        ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name:
          """The default time-to-live for a users' API secret, in seconds (for
          example, 3600 seconds = 1 hour).""",

        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name:
          """The default point cost threshold for buggies: you can always
          override this when you create each race.""",

        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name:
          """Races are grouped by league, so if you're using that mechanism you
          can nominate the league that new races are in here. It's common to
          run the race server without using leagues, so if you're not sure,
          leave this blank.""",
          # note: leagues not implemented yet: this isn't shown because
          #       the config setting is excluded from the "Race" group

        ConfigSettingNames.EXT_ID_EXAMPLE.name:
          """If users have an external ID, provide an example of what it might
          look like. This setting is ignored if `USERS_HAVE_EXT_ID` is `No`.""",

        ConfigSettingNames.EXT_ID_NAME.name:
          """If user have an external ID, what is it called? For example:
          "Student number", "Moodle ID", "Blackboard ID", "Canvas ID". This
          setting is ignored if `USERS_HAVE_EXT_ID` is `No`.""",

        ConfigSettingNames.EXT_USERNAME_EXAMPLE.name:
          """If users have an external username, provide an example format
          (e.g., `abcd123` or `ada@example.org`). Note that this only serves as
          a placeholder suggestion when inputting — it's not used to validate
          or force the format of inputs. This setting is ignored if
          `USERS_HAVE_EXT_USERENAME` is `No`.""",

        ConfigSettingNames.EXT_USERNAME_NAME.name:
          """If users have an external username, what is it called? For
          example: "College username". This is to clearly differentiate the
          race server username (which students use to log into this race
          server) from this external one (which they presumably use to access
          other course systems). Keep it short, because it's used on buttons in
          the admin. This setting is ignored if `USERS_HAVE_EXT_USERENAME` is
          `No`.""",

        ConfigSettingNames.GITHUB_CLIENT_ID.name:
          """The GitHub client ID for the GitHub app that the server uses to
          fork the buggy editor repo into a student's own GitHub account.""",

        ConfigSettingNames.GITHUB_CLIENT_SECRET.name:
          """A string that exactly matches the client secret stored on the
          GitHub app that the server uses to fork the buggy editor repo into a
          student's own GitHub account. You only need this if
          `IS_USING_GITHUB_API_TO_FORK` is `Yes`.""",

        ConfigSettingNames.INSTITUTION_FULL_NAME.name:
          """Full name for your institution, college, or school.""",

        ConfigSettingNames.INSTITUTION_HOME_URL.name:
          """Full URL for the home page of your institution: used as a link on
          the race server's home page.""",

        ConfigSettingNames.INSTITUTION_SHORT_NAME.name:
          """Short name or abbreviation for your institution, college, or
          school.""",

        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name:
          """Choose `Yes` if all the config settings' values should be
          available when publishing tech notes. This setting is only relevant
          if you're customising the tech notes and/or publishing them
          externally. If `No`, only (sensible) selected config settings will be
          available as substitutions in the tech notes' markdown. See the
          Pelican config file(s) for details.""",

        ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name:
          """Is the API secret _always_ a one-time password? If it is, it won't
          work after the first success (and needs to be reset). This does not
          affect the time-to-live of the secret. The default settings of this
          and `IS_STUDENT_API_OTP_ALLOWED` (`No` and `Yes` respectively) mean
          OTPs are not used except where students enable them on their own
          accounts.""",

        ConfigSettingNames.IS_BUGGY_DELETE_ALLOWED.name:
          """Can a student delete their buggy? If not, the buggy exists once
          they've uploaded JSON data for it, and remains until changed by
          subsequent uploads (which is encouraged). This setting only controls
          whether students should be able to delete their own buggies (admins
          always can). If in doubt, choose `No`.""",

        ConfigSettingNames.IS_DNF_POSITION_DEFAULT.name:
          """Is a **Did not Finish** race result still given an ordinal
          position (based on how far the buggy _did_ travel before it
          stopped)? It's common in motorsport to not grant a position to a
          racer who did not complete the necessary number of laps... but in
          buggy racing, buggies can more easily run out of fuel, especially
          early in the project when nobody knows how much petrol or how many
          hamsters you need to get round a track. So choose `Yes` if you want
          to avoid demoralising students for mishaps during races. This is
          the default for your project and you can override it on a
          race-by-race basis.""",

        ConfigSettingNames.IS_FAKE_LATEX_CHOICE_ENABLED.name:
          """The tech notes are static pages, rendered on a dark background (to
          clearly distinguish from the race server's pages). If you choose
          `Yes`, this option adds a small button to the bottom right-hand
          corner of each page that toggles the style between the dark style,
          and a simulation of a classic page created with LaTeX, the excellent
          typesetting system beloved of academics. Because the tech notes are
          static content, this CSS toggle is implemented in JavaScript. This
          feature is an in-joke that only need be engaged if you are feeling
          playful, or if there are academics in your institution who might be
          horrified by the prospect of reading text on anything other than
          crisp white paper in Computer Modern font.""",

        ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name:
          """Choose `Yes` if you need Windows newlines at the end of each line
          of the task issues CSV file (you probably don't need to change
          this).""", # NB: possibly needed for GitHub API?

        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name:
          """Should usernames (which are always lower case) be displayed using
          title case? For example, choose `Yes` if the usernames you're using
          are effectively students' names. Login is always case insensitive, so
          this only affects how usernames are displayed, not what users need to
          type.""",

        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name:
          """Typically, students are expected to submit their projects as a zip
          file containing the buggy editor web app (including a report/poster,
          if you've enabled it). The project page will display general
          information about those files (e.g., they should have the student's
          name just in case your submission process doesn't capture that: you
          end up with a lot of zip files with the same name otherwise). Use
          this setting to display or hide this general information on the
          "project" page. If set to `Yes`, remember to check that the text that
          appears on the project page does indeed make sense to students.""",

        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name:
          """Normally, only a logged-in administrator who knows the
          `AUTHORISATION_CODE` can register new users. But if you accidentally
          end up unable to log in (deleted/demoted user, forgotten password)
          set this to `Yes` (or `1`) as an environment variable to allow
          **emergency access** to the registration page, and create a new
          (admin) user. You'll also need to know the auth code (which can also
          be set via an environment variable if it's been lost).""",

        ConfigSettingNames.IS_RACE_FILE_START_STAMPED.name:
          """Do you want the race start (date+time) to appear in the filename
          when you download a race file? You might not need this if your races
          always have recognisably unique titles.""",

        ConfigSettingNames.IS_RACE_FILE_DATE_STAMPED.name:
          """Do you want a datestamp (when you downloaded it) to appear in the
          filename when you download a race file?""",

        ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name:
          """Should a race be public as soon as you create it? If you choose
          `No`, you'll have to remember to publish a race in order for students
          to see it.""",

        ConfigSettingNames.IS_REDIRECT_HTTP_TO_HTTPS_FORCED.name:
          """Should the webserver itself force HTTPS? **Be careful**: this
          setting will not be helpful if your hosting environment manages this
          for you (that is, only set this to `Yes` if you are certain HTTPS
          requests arrive directly to the app: if you have a process that's
          handling requests and connecting with this app locally over HTTP,
          forcing redirects with this setting may prevent _any_ requests
          getting through). HTTPS is mandatory for GitHub's OAuth
          authentication, or if you're holding any personal information on
          students... but _this setting does not implement HTTPS_ — it only
          forces redirection if the protocol the app sees in incoming requests
          is (non-secure) HTTP.""",

        ConfigSettingNames.IS_SHOWING_RESTART_SUGGESTION.name:
          """Do you want the server to suggest you restart it after changing
          any config settings? Our experience is that normally changing config
          does not require a restart _but_ in case your implementation would
          benefit from this, you can switch the suggestions on.""",

        ConfigSettingNames.IS_SHOWING_EXAMPLE_RACETRACKS.name:
          """Do you want the admin interface to include the example racetracks?
          If you are certain you only want to use your own custom racetracks,
          you can choose `No` to hide the button that adds the pre-built
          examples. Unless you've already built your racetracks, you should
          almost certainly choose `Yes`.""",

        ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name:
          """It can be helpful for students to have a summary of the workflow
          process. If you set `IS_SHOWING_PROJECT_WORKFLOW` to `Yes` then the
          server will show either the default workflow page, or an external one
          if you specify `PROJECT_WORKFLOW_URL`. If you do choose to display
          the workflow page, when it's published take a moment to read it to
          confirm it matches what you expect your students to do.""",

        ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name:
          """The task list and tech notes do not get updated when you change
          config (or edit tasks): adopt the discipline of manually publishing
          them whenever you change config (which usually only happens before
          project has started). However, if you're hosting the server on a
          system with an ephemeral file system, static content (including the
          buggy editor zipfile, if you're serving that) will not survive a 
          restart. Set `IS_STATIC_CONTENT_AUTOGENERATED` to automatically
          re-publish any static content when the server starts up. Note that
          this only _re-publishes_ (by inspecting timestamps). If you're
          hosting on a basic Heroku installation, switch this to `Yes`. If
          you've got a peristent file system (that includes Docker, because
          the `published` directory is a shared volume for this reason),
          choose `No`.""",

        ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name:
          """When you upload race files (primarily for replaying races), do you
          want to store them here on the race server, in the database? If you
          don't, you'll need to publish them online somewhere which has a
          friendly CORS policy (GitHub pages works fine), and make sure you
          store the URL correctly when you update the race. If you're running
          an especially large project or little server, there may be efficiency
          benefits in _not_ using the database, but otherwise it's simplest to
          to choose `Yes`. """,

        ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name:
          """Do you want students to be able to record text on this server
          reporting they approached/did each task? If you're running the
          project with a report (see `PROJECT_REPORT_TYPE`), then this allows
          students to save notes here as they go along, which in turn gives you
          some visibility of their progress (which is why we implemented it).
          If you choose `No`, this feature will be hidden. Note that you _can_
          choose `Yes`, letting students store task texts, even if the project
          doesn't require a report.""",

        ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name:
          """Can individual students choose to set their own API secret to be
          different from the default one-time-password behaviour you've set
          with `IS_API_SECRET_ONE_TIME_PW`? For example, it's a little simpler
          for students to get the API working if it's not an OTP — but by
          setting this to `Yes` they can opt in or out.""",

        ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name:
          """Should students fork the buggy editor repo into their own GitHub
          repo? Choose `No` if your students are not using GitHub. If you
          choose `Yes`, make sure you've set `IS_USING_GITHUB_API_TO_FORK` if
          you want this to be automated via the race server. This setting only
          affects whether mentions of GitHub should be removed in instructions
          on the server, and is ignored if `IS_USING_GITHUB` is `No`.""",
        
        ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name:
          """Teaching Assistants cannot edit user data. But do you want TAs to
          be able to add or edit comments left by staff?""",

        ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name:
          """Administrators can change all other users' passwords. Choose `Yes`
          if you also want Teaching Assistants to be able to change (non-staff)
          users' passwords. Note that students who forget their passwords
          cannot reset them, and will need to ask a staff member to do it — so
          enabling TAs might be helpful. Changing a student's password does not
          require the auth code.""",

        ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name:
          """By default, task URLs go direct to the server (e.g.,
          `/project/tasks/3-multi`) which then redirects to an anchor within
          the all-tasks page (e.g., `/project/tasks#task-3-multi`). This works
          fine on this server and makes "nicer" URLs, but if you don't like
          this behaviour, choose `Yes` to have any generated links go directly
          to the anchor tag.""",

        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name:
          """The admin interface normally lets you publish the tech notes, but
          if you're hosting them externally this might be confusing (because it
          certainly won't be changing your external site). However, there are
          circumstances where you want to be able to publish them here too,
          depending on how you're managing their creation. This setting doesn't
          affect the display of tech notes (see `TECH_NOTES_EXTERNAL_URL`),
          only whether the interface for publishing them is shown.""",

        ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name:
          """When you publish race results, are usernames (as well as the
          buggies' pennants) shown?""",

        ConfigSettingNames.IS_USING_GITHUB.name:
          """Are you using GitHub to distribute the source code for the buggy
          editor to students? If you choose `Yes` there is still quite a lot of
          flexibility as to how it's implemented (from simply downloading from
          GitHub to automatically forking it into their GitHub account). If you
          choose `No`, the students can download a zip file from this server
          (or you can override this with your own copy).""",

        ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name:
          """If students must work with the buggy editor in their own GitHub
          repo, the race server can help by automatically forking it for them,
          using the GitHub API. You must configure the `GITHUB_CLIENT_ID` and
          `GITHUB_CLIENT_SECRET` for this to work (and `IS_USING_GITHUB` and
          `IS_STUDENT_USING_GITHUB_REPO` must both be `Yes`).""",

        ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name:
          """If you have set the race server to use GitHub's API to fork the
          buggy editor repo into each student's account, it will also also
          inject the tasks as GitHub issues into their repo unless you prevent
          it here. This setting is ignored unless both `IS_USING_GITHUB` and
          `IS_USING_GITHUB_API_TO_FORK` are both set to `Yes`. """,

        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name:
          """If your students will be using a remote server (see:
          `PROJECT_REMOTE_SERVER_NAME`) and are running VS Code over a remote
          session, the race server can produce a VS Code workspace file to
          facilitate cloning the repo onto that server and subsequently access
          it through VS Code. This is quite a specific setup: if you're not
          sure, you almost certainly do not want this. """,

        ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name:
          """If you publish the buggy editor app on this server, should the
          `BUGGY_RACE_SERVER_URL` be written into `app.py`? This setting
          won't be used if you don't generate the zipfile on this server
          (for example, if `IS_USING_GITHUB` is `Yes`) but remember you or
          your students do need to change it inside the buggy editor source
          code eventually.""",

        ConfigSettingNames.PROJECT_CODE.name:
          """If this project is known by a course or module code, use it (for
          example, when we ran it at Royal Holloway, it was CS1999). See also
          `PROJECT_SLUG` which is how this code may appear in filenames of any
          downloaded files, if you need it to be different. The full name of
          the project is \"the `PROJECT_CODE` Buggy Racing project\", so if you
          don't have or need a course code, it's fine to leave it blank.""",

        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name:
          """This is the minimum phase you'd expect an inexperienced programmer
          who's fully engaged in the project to have completed before running
          out of time. The default of 3 is based on our experience of running a
          6-week project (several times) with students with only one term's
          prior experience of Python, and takes into account that task 3-MULTI
          is (deliberately) more involved than most students realise. This
          expectation is displayed to students (for example on the task list
          page). If you don't want this, set it to zero to remove the
          recommendation entirely.""",

        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name:
          """If students are going to develop on a remote server, what is its
          address? This is used with their external username (or just username,
          if they haven't got one): for example enter `linux.example.ac.uk` so
          student Ada can log in via `ada@linux.example.ac.uk`. If you're not
          using a remote project server, leave this blank (see also
          `PROJECT_REMOTE_SERVER_NAME`).""",

        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name:
          """If students are going to develop on a remote server, what is its
          (human-facing) name? This is used to help students identify the
          server they are logging into (e.g, "the CompSci department's Unix
          server"). Leave this blank if your students are all working on their
          own machines (i.e., not a single teaching server with login accounts,
          python, and personalised HTTP ports).""",

        ConfigSettingNames.PROJECT_REMOTE_SERVER_APP_URL.name:
          """If students are going to develop on a remote server, what is the
          URL then need to hit in their browser to see their app? Presumably it
          will have a custom port on the end too. If you're not using a remote
          project server, leave this blank.""",

        ConfigSettingNames.PROJECT_REPORT_TYPE.name:
          """If you require students to include a report of how they tackled
          the tasks, indicate that here ("report" or "poster" are just
          different names for the same thing, due to an historic anomaly). The
          report takes the form of an additional webpage in the student's buggy
          editor webserver. If you choose `No report`, all mentions will be
          removed: see also the `IS_STORING_STUDENT_TASK_TEXTS` setting in the
          **Tasks** group of settings. """,

        ConfigSettingNames.PROJECT_SLUG.name:
          """This is how the `PROJECT_CODE` appears — as a prefix — in any
          filenames that are downloaded from the server. This is a kindness to
          help disambiguate files in your Downloads folder. If you leave this
          blank, it will default to using an automatic "slugged" version of
          your project code, if any. Note that there are some places where
          students can download files (e.g., tabulated specification data) too,
          so it's not just admin staff who will see it.""",

        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name:
          """If you require all students to submit their projects on a specific
          deadline, set it here. This is displayed prominently (if the project
          is enabled) on the project page, but isn't currently used by the
          server for anything else. Avoid using 00:00 as a time because it
          confuses students — 23:59 is clearer (and 16:00 is healthier). Leave
          blank if you don't want to display a deadline at all (remember you
          can also use Announcements).""",

        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name:
          """Provide a link to either the web page where you'll be accepting
          submissions (presumably zip files) or else a page containing clear
          instructions for the students to follow. The buggy race server does
          not handle submissions itself. By default, no submission information
          is provided (because it's very dependent on each institution), which
          means no link is displayed: so you must supply one yourself.""",

        ConfigSettingNames.PROJECT_WORKFLOW_URL.name:
          """You can replace the default workflow page with a redirection to
          one you've customised (and hosted elsewhere). If you leave this
          setting blank, the default page will be shown. In either case, this
          setting is ignored if `IS_SHOWING_PROJECT_WORKFLOW` is `No`.""",

        ConfigSettingNames.PROJECT_ZIP_NAME_TYPE.name:
          """Normally the suggested filename for submissions (the students' zip
          file) is their username + `.zip`. But if you prefer your students to
          use an external username or ID, you can suggest it here. If you pick
          a type that users don't have, it will fall back to `username`
          (because all users have one). This setting is ignored if
          `IS_PROJECT_ZIP_INFO_DISPLAYED` is `No`.""",

        ConfigSettingNames.SECRET_KEY.name:
          """A secret used by the webserver in cookies, etc. This should be
          unique for your server: the default value shown here was randomised
          on installation, so you usually don't need to change it. Note that
          changing it will almost certainly break existing sessions. For
          cleanest results, reboot the server as soon as you've changed it).""",

        ConfigSettingNames.SOCIAL_0_NAME.name:
          """Name (shown on button)""",
        ConfigSettingNames.SOCIAL_0_TEXT.name:
          """Short description""",
        ConfigSettingNames.SOCIAL_0_URL.name:
          """Full URL to external site/resource""",
        ConfigSettingNames.SOCIAL_1_NAME.name:
          """Name (shown on button)""",
        ConfigSettingNames.SOCIAL_1_TEXT.name:
          """Short description""",
        ConfigSettingNames.SOCIAL_1_URL.name:
          """Full URL to external site/resource""",
        ConfigSettingNames.SOCIAL_2_NAME.name:
          """Name (shown on button)""",
        ConfigSettingNames.SOCIAL_2_TEXT.name:
          """Short description""",
        ConfigSettingNames.SOCIAL_2_URL.name:
          """Full URL to external site/resource""",
        ConfigSettingNames.SOCIAL_3_NAME.name:
          """Name (shown on button)""",
        ConfigSettingNames.SOCIAL_3_TEXT.name:
          """Short description""",
        ConfigSettingNames.SOCIAL_3_URL.name:
          """Full URL to external site/resource""",

        ConfigSettingNames.SUPERBASICS_URL.name:
          """There are a few places (for example in the workflow page and the
          tech notes) that link to a "superbasics" site which explains basic
          concepts for students. You can use the default, but you can also fork
          it and customise it, in which case put its URL here. Note that the
          links are to specific paths within the superbasics, which are added
          to this base URL, so if you host your own version be cautious about
          changing existing paths within it.""",

        ConfigSettingNames.TASK_NAME_FOR_API.name:
          """The name of the task that require use of the upload API. If set,
          this is shown as a helpful link in the explanatory text on the
          student's API settings page. If you set this to be empty, no link is
          shown. You can provide multiple task names by separating them with
          commas. If you haven't customised the task list, you don't need to
          change this.""",

        ConfigSettingNames.TASK_NAME_FOR_ENV_VARS.name:
          """The name of the task for setting environment variables. If you
          haven't customised the task list, you don't need to change this. """,

        ConfigSettingNames.TASK_NAME_FOR_GET_CODE.name:
          """The name of the task for getting the source code. If you haven't
          customised the task list, you don't need to change this.""",

        ConfigSettingNames.TASK_NAME_FOR_VALIDATION.name:
          """The name of the task that requires use of validation. If set, this
          is shown as a helpful link in the explanatory text on the reports
          page. If you haven't customised the task list, you don't need to
          change this.""",

        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name:
          """Full URL to the tech notes pages if they are *not* being hosted on
          this server. If you've customised them and have published them
          somewhere else (for example, hosted on GitHub pages), then put the
          URL here. By default, tech notes are hosted on the race server, so
          you can leave this blank.""",

        ConfigSettingNames.USER_ACTVITY_PERIOD_S.name:
          """The period (in seconds) over which each logged-in user's activity
          is logged. Pragmatically, this avoids updating the database on every
          request, because usually you're only concerned about whether or not a
          student has logged in recently, not the accuracy of the timestamp.
          This updates the "last activity" timestamp if the user sends a
          request this-number-of-seconds since the last recorded activity.""",

        ConfigSettingNames.USERNAME_EXAMPLE.name:
          """A placeholder string used in the login form. This can be
          especially helpful if students use a different username for accessing
          other college systems. You can set this to be blank.""",

        ConfigSettingNames.USERS_HAVE_EXT_ID.name:
          """Do users have an ID from an external system? This might be useful
          if you want to match students with their existing ID on another
          system like Moodle, Blackboard or Canvas. You don't need this unless
          it's a useful way of identifying a student. If you do set this to
          `Yes`, you should also set `EXT_ID_NAME` to describe what it is.""",

        ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name:
          """Do users have an external username or account that's specific to
          your organisation or institution? You might not need this, or you
          might already be using it as the username — in which case choose
          `No`. Note: the race server does **not** use this for authentication
          (i.e., there is no OAuth implementation). However, if your users need
          to log into a remote server for development _and_ you are using VS
          Code workspace files, you will need this to be `Yes` — unless you're
          simply using those external usernames as the students' race server
          usernames when you register them.""",

        ConfigSettingNames.USERS_HAVE_EMAIL.name:
          """Do users need email addresses? The server doesn't send emails so
          you don't need this field unless it's a useful way of identifying a
          student.""",

        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name:
          """Do users need to have a first name? You might be using each
          student's first name as the username, in which case you don't need
          this.""",

        ConfigSettingNames.USERS_HAVE_LAST_NAME.name:
          """Do users need to have a last name? If you can already identify
          your students from the other fields, you might not need this.""",

    }

    SETUP_GROUP_DESCRIPTIONS = {
      ConfigGroupNames.AUTH.name:
        """You must complete the setup. It takes around 5–10 minutes, and you
        may be able to leave most settings to their defaults (and you can
        change most things later, if you need to).""",

      ConfigGroupNames.GITHUB.name:
        """Setup the GitHub details here. If you're injecting issues into
        student's own repos, you must provide valid GitHub client details which
        may be specific to your installation. If you are not using Git or
        GitHub, the first three settings are used (that is, don't be fooled by
        the "GitHub" name of this group!).""",

      ConfigGroupNames.ORG.name:
        """Provide general details about your institution/organisation.""",

      ConfigGroupNames.PROJECT.name:
        """These settings control aspects of the what the students need to do
        (for example: are they only coding, or do you want them to add a
        report/poster page to their buggy editor too?). If you or your
        department is running a remote server on which students will be doing
        their Python, enter its details here (there's extra set-up required on
        that remote server too — see the docs). It's fine to run the project
        without a remote server: it just means students work on individual
        machines.""",

      ConfigGroupNames.RACES.name:
        """Race settings can all be left to default (you can change them
        later if you need to).""",

      ConfigGroupNames.SERVER.name:
        """These settings control the behaviour of the server. The
        BUGGY_RACE_SERVER_URL setting is critically important, whereas you may
        find you can accept the defaults for most or all of the others here.""",

      ConfigGroupNames.SOCIAL.name:
        """These are used to add links to your institution's social or
        educational accounts. If you run support sites like Moodle or Discord
        or Teams for this project, add them here.""",

      ConfigGroupNames.TASKS.name:
        """The work the students must do to develop their buggy editor is
        divided into named tasks. Tasks are grouped into phases (for example
        phase 0 is all about getting and running the basic code). The default
        project has around 26 tasks, but you can change any and all of this
        once you've completed this config setup. The tasks are published as a
        task list that itself depends on other config settings, so you'll need
        to publish the task list once you've finished — or if you change any
        settings in the future.""",

      ConfigGroupNames.TECH_NOTES.name:
        """The tech notes are static webpages with supporting or explanatory
        material specific to the project, and even some tasks. You cannot
        customise them on this server (i.e., through this web interface) but
        you can host them externally (e.g., on your own course website or
        GitHub pages), in which case set the external URL here. For details on
        how to extract the tech notes for self-publication, see separate docs.
        Like the task list, the tech notes depend on other config settings, so
        you need to publish them once you've finished — or if you change any
        settings in the future""",

      ConfigGroupNames.USERS.name:
        """Every student will need a username. These settings define what
        fields you want to store IN ADDITION to that username. You do not need
        to have any additional fields (we recommend you only add them if you
        really need to, for example, if the usernames aren't already the
        students' first names, maybe add a first name so you can recognise who
        they are). Only admin users see these additional fields — they aren't
        made public.""",
    }

    NO_KEY = "_NOTHING_" # special case of unexpected config with no key

    # config key for list of config settings that are being overridden by
    # declarations in the environment (e.g., from .env)
    ENV_SETTING_OVERRIDES_KEY = "_ENV_OVERRIDES"

    # config key for list of config settings that are found in the database
    # but aren't used (e.g., deprecated config no longer used)
    UNEXPECTED_SETTINGS_KEY = "_UNEXPECTED_CONFIG_SETTINGS"

    # config key for cachebuster: a number expected to be different each run
    CACHEBUSTER_KEY = "_CACHEBUSTER"

    # config keys for forcing the database URI's password to be rewritten
    # and adding sslmode=require
    # as a query variables (which are not stored in the database: must be read
    # from the environment, because it happens before db connection is made)
    REWRITING_DB_URI_PASSWORD_KEY = "IS_REWRITING_DB_URI_PW_AS_QUERY"
    FORCED_DB_URI_SSL_MODE_KEY = "FORCED_DB_URI_SSL_MODE"
    BYPASSING_DB_CONFIG_KEY = "IS_BYPASSING_DB_CONFIG"

    # SQLAlchemy database URL may differ from the "source" DATABASE_URL
    # because (for example) Heroku's DATABASE_URL's Postgres protocol
    # name is different from what SQLAlchemy needs
    SQLALCHEMY_DATABASE_URI_KEY = "SQLALCHEMY_DATABASE_URI"

    @staticmethod
    def is_valid_name(name):
      return name in ConfigSettings.DEFAULTS
  
    @staticmethod
    def prettify(name, value):
      if ConfigSettings.TYPES.get(name) == ConfigTypes.BOOLEAN:
        return "No" if (value == "0" or not bool(value)) else "Yes"
      return value

    @staticmethod
    def get_pretty_defaults():
        return {
            name: ConfigSettings.prettify(name, ConfigSettings.DEFAULTS[name])
            for name in ConfigSettings.DEFAULTS
        }

    @staticmethod
    def pretty_group_name(name):
       """ Because Tom complained about the Github/GitHub case """
       if name == "GITHUB":
          return "GitHub"
       else:
          return name.title().replace("_", " ")

    @staticmethod
    def stringify(name, value):
      """ Get string suitable for saving to database. """
      if value is None:
        return ""
      if ConfigSettings.TYPES.get(name) == ConfigTypes.BOOLEAN:
        return "1" if value else "0"
      return str(value)

    @staticmethod
    def get_dict_declaration(name, value):
      """ Used in Pelican conf files, within dictionary """
      type = ConfigSettings.TYPES.get(name)
      str_value = str(value)
      if type in [ConfigTypes.PASSWORD, ConfigTypes.SENSITIVE_STRING]:
        str_value = None
      elif type is None or type in (
         ConfigTypes.DATETIME,
         ConfigTypes.STRING,
         ConfigTypes.URL,
         ConfigTypes.TIMEZONE,
        ):
        str_value = str_value.replace("\"", "\\\"").replace("\n", " ")
        str_value = f"\"{str_value}\""
      return f"\"{name}\": {str_value},"

    @staticmethod
    def set_config_value(app, name, value):
        """ Sets config value in the app (casting to correct type)
            Note: this does NOT do anything with the database!
        """
        str_value = str(value)
        if not ConfigSettings.is_valid_name(name):
            if name == "": name = ConfigSettings.NO_KEY
            unexpecteds = app.config.get(ConfigSettings.UNEXPECTED_SETTINGS_KEY)
            if unexpecteds is None:
               app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY] = [name]
            elif name not in unexpecteds:
               app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY].append(name)
            print(f"* ignoring unknown config setting: {name}, not set", flush=True)
            return
        type = ConfigSettings.TYPES.get(name) or ConfigTypes.STRING
        if type == ConfigTypes.BOOLEAN:
            value = str_value == "1"
        elif type == ConfigTypes.INT:
            value = int(str_value) if str_value.isdecimal() else 0
        elif type == ConfigTypes.TIMEZONE:
            try:
               value = pytz.timezone(str_value)
            except:
               print(f"* unrecognised timezone: {str_value}")
               value = pytz.utc
        app.config[name] = value

    @staticmethod
    def users_additional_fieldnames_is_enabled_dict(app):
        return {
            "email": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_EMAIL.name)
            ),
            "ext_id": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_EXT_ID.name)
            ),
            "ext_username": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name)
            ),
            "first_name": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_FIRST_NAME.name)
            ),
            "last_name": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_LAST_NAME.name)
            ),
        }

    @staticmethod
    def users_additional_fieldnames(app):
        is_enabled_dict = ConfigSettings.users_additional_fieldnames_is_enabled_dict(app)
        return [ field for field in is_enabled_dict if is_enabled_dict[field] ]


class AnnouncementTypes(Enum):
    """ Control what announcements are supported, and where they go """
    ABOUT = 'about'
    DANGER = 'danger'
    GET_EDITOR = 'get-editor'
    INFO = 'info'
    LOGIN = 'login'
    SPECIAL = 'special'
    TAGLINE = 'tagline'
    WARNING = 'warning'

    @staticmethod
    def get_top_of_page_types():
        return [
          AnnouncementTypes.DANGER.value,
          AnnouncementTypes.INFO.value,
          AnnouncementTypes.SPECIAL.value,
          AnnouncementTypes.WARNING.value,
        ]

    @staticmethod
    def get_local_types():
        return [
            ann_type.value for ann_type in AnnouncementTypes
            if ann_type.value not in AnnouncementTypes.get_top_of_page_types()
        ]


##################################################################

env = Env()
env.read_env()

class ConfigFromEnv():

    # current version (sanity check vs. git)
    _VERSION_IN_SOURCE = MANUAL_LATEST_VERSION_IN_SOURCE

    # set up phase:
    # 0 - all done! (admin has full access to settings)
    # 1 - force change of auth code, get admin username and password
    # 2+ - subsquent settings (broken down into groups)
    _SETUP_STATUS = env.str(str(ConfigSettingNames._SETUP_STATUS), default=None)

    # announcement constant, used in layout template
    _ANNOUNCEMENT_TOP_OF_PAGE_TYPES = AnnouncementTypes.get_top_of_page_types()

    # some (not-buggy-race-specific) config _only_ comes from the ENV
    FLASK_APP = env.str("FLASK_APP", default="buggy_race_server/app.py")
    FLASK_ENV = env.str("FLASK_ENV", default="production")
    DEBUG = FLASK_ENV == "development"
    FLASK_DEBUG = DEBUG

    UPLOAD_FOLDER = "buggy_race_server/uploads"

    LOG_LEVEL = env.str("LOG_LEVEL", default="debug")
    BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
    DEBUG_TB_ENABLED = DEBUG
    DEBUG_TB_INTERCEPT_REDIRECTS = env.bool("DEBUG_TB_INTERCEPT_REDIRECTS", default=False)
    CACHE_TYPE = env.str("CACHE_TYPE", default="simple") # Can be "memcached", "redis", etc.

    SQLALCHEMY_TRACK_MODIFICATIONS = env.bool("BCRYPT_LOG_ROUNDS", default=False)

    # In production, set to a higher number, like 31556926
    SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT", default=43200)

    DATABASE_URL = env.str("DATABASE_URL")

    GUNICORN_WORKERS = env.int("GUNICORN_WORKERS", default=1)
    
    # handily makes all downloaded JSON pretty:
    # less confusing for students (e.g., downloading spec files)
    JSONIFY_PRETTYPRINT_REGULAR = True

    _UNEXPECTED_CONFIG_SETTINGS = []

    # must set SECRET_KEY for sessions to work, and must
    # be in place here in case subsequent (db) load doesn't load it
    SECRET_KEY = ConfigSettings.DEFAULTS[ConfigSettingNames.SECRET_KEY.name]

    def __init__(self):
      # In addition to the Flask/server "system" environment variable,
      # *any* config setting can be overridden here too.
      # This allows sysadmin to punch past a bad setting that's got into
      # the database (e.g., goofing up the admin user list could be a problem)
      # although in normal use everything can/should be done through the
      # database (i.e., through the web interface in admin/settings) 
      # By putting the env names into ENV_SETTING_OVERRIDES_KEY, the settings
      # pages can usefully indicate when these have been overridden: this
      # matters because any changes to the database settings table won't
      # persist if it's being overridden by an ENV declaration at start-up.
      env_setting_overrides = []
      for name in ConfigSettings.DEFAULTS:
          setting_value = env.str(name, default=None)
          if setting_value is not None:
              if ConfigSettings.TYPES.get(name) == ConfigTypes.PASSWORD:
                 setting_value = bcrypt.generate_password_hash(setting_value).decode('utf8')
              setattr(self, name, setting_value)
              env_setting_overrides.append(name)
      self.__setattr__(ConfigSettings.ENV_SETTING_OVERRIDES_KEY, env_setting_overrides)
      self.__setattr__(ConfigSettings.CACHEBUSTER_KEY, int(time()))

      # Some shenanigans here because since upgrading Flask, we've seen
      # access only working if the password is passed as a query variable
      # on the end of the database URI, which isn't how heroku presents it

      is_rewriting_db_uri_pw_as_query = env.bool(
          ConfigSettings.REWRITING_DB_URI_PASSWORD_KEY,
          False
      )
      self.__setattr__(
        ConfigSettings.REWRITING_DB_URI_PASSWORD_KEY,
        is_rewriting_db_uri_pw_as_query
      )

      forced_db_uri_ssl_mode_key = env.str(
          ConfigSettings.FORCED_DB_URI_SSL_MODE_KEY,
          ""
      )

      self.__setattr__(
        ConfigSettings.FORCED_DB_URI_SSL_MODE_KEY,
        forced_db_uri_ssl_mode_key
      )

      self.__setattr__(
        ConfigSettings.BYPASSING_DB_CONFIG_KEY,
        env.str(
          ConfigSettings.BYPASSING_DB_CONFIG_KEY,
          None
        )
      )

      sqlalchemy_database_uri = self.DATABASE_URL
      if sqlalchemy_database_uri.startswith('postgres://'):
          # Heroku produces database URL with postrgess:// prefix, but
          # SQLAlchemy needs postgresql:// ... so fix it up
          sqlalchemy_database_uri = sqlalchemy_database_uri.replace(
              'postgres://',
              'postgresql://'
          )

      if is_rewriting_db_uri_pw_as_query:
          DATABASE_RE = re.compile(r"^([^:]+:[^:]+):([^@]+.)(@\w+[^?]+)(\?.*)?")
          # 1=method+user, 2=password, 3=host, 4=query params (if any)
          if match := re.match(DATABASE_RE, sqlalchemy_database_uri):
              sqlalchemy_database_uri = match.group(1)+match.group(3)
              sqlalchemy_database_uri += "&" if match.group(4) else "?"
              sqlalchemy_database_uri += f"password={match.group(2)}"

      # forcing sslmode (probably to "require") by adding it as a query param
      if forced_db_uri_ssl_mode_key:
          # TODO presupposes no '?' in password
          if "?" not in sqlalchemy_database_uri:
              sqlalchemy_database_uri += "?"
          else:
              sqlalchemy_database_uri += "&"
          sqlalchemy_database_uri += f"sslmode={forced_db_uri_ssl_mode_key}"

      self.__setattr__(
        ConfigSettings.SQLALCHEMY_DATABASE_URI_KEY,
        sqlalchemy_database_uri
      )
