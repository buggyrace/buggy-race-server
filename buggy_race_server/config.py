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
import re
from os import path
from buggy_race_server.extensions import bcrypt

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

    # Name of the CSV file into which tasks-as-issues (for GitHub) are put
    _BUGGY_EDITOR_ISSUES_FILE = auto()

    # Current announcements are cached to avoid database reads on every hit
    _CURRENT_ANNOUNCEMENTS = auto()

    # Settings that are being overridden by ENV variables (by this class)
    # are noted here so a warning can be displayed on the settings page
    _ENV_SETTING_OVERRIDES = auto()

    # Path where published HTML (task list and tech notes) is written
    _PUBLISHED_PATH = auto()

    # Setup status is used to track progress (and ultimately completion)
    # of the setup process when the app is first installed
    _SETUP_STATUS = auto()

    # Timestamps that user never sets explicitly, but are stored as config
    _TASK_LIST_GENERATED_DATETIME = auto()
    _TASKS_LOADED_DATETIME = auto()
    _TECH_NOTES_GENERATED_DATETIME = auto()

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

    # User-editable config settings: presented in the settings/config.
    # Each one should also exist in a settings group, and have a description
    # and a type.
    ADMIN_USERNAMES = auto()
    AUTHORISATION_CODE = auto()
    AUTO_GENERATE_STATIC_CONTENT = auto()
    BUGGY_EDITOR_GITHUB_URL = auto()
    BUGGY_EDITOR_REPO_NAME = auto()
    BUGGY_EDITOR_REPO_OWNER = auto()
    BUGGY_RACE_SERVER_URL = auto()
    DEFAULT_RACE_COST_LIMIT = auto()
    DEFAULT_RACE_IS_VISIBLE = auto()
    DEFAULT_RACE_LEAGUE = auto()
    FORCE_REDIRECT_HTTP_TO_HTTPS = auto()
    GITHUB_CLIENT_ID = auto()
    GITHUB_CLIENT_SECRET = auto()
    INSTITUTION_FULL_NAME = auto()
    INSTITUTION_HOME_URL = auto()
    INSTITUTION_SHORT_NAME = auto()
    IS_ALL_CONFIG_IN_TECH_NOTES = auto()
    IS_PRETTY_USERNAME_TITLECASE = auto()
    IS_PROJECT_ZIP_INFO_DISPLAYED = auto()
    IS_PUBLIC_REGISTRATION_ALLOWED = auto()
    IS_STORING_STUDENT_TASK_NOTES = auto()
    IS_TECH_NOTE_PUBLISHING_ENABLED = auto()
    IS_USING_REMOTE_VS_WORKSPACE = auto()
    PROJECT_CODE = auto()
    PROJECT_PHASE_MIN_TARGET = auto()
    PROJECT_REMOTE_SERVER_ADDRESS = auto()
    PROJECT_REMOTE_SERVER_NAME = auto()
    PROJECT_REPORT_TYPE = auto()
    PROJECT_SLUG = auto()
    PROJECT_SUBMISSION_DEADLINE = auto()
    PROJECT_SUBMISSION_LINK = auto()
    PROJECT_WORKFLOW_URL = auto()
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
    TASK_NAME_FOR_API = auto()
    TASK_URLS_USE_ANCHORS = auto()
    TECH_NOTES_EXTERNAL_URL = auto()
    USERS_HAVE_EMAIL = auto()
    USERS_HAVE_FIRST_NAME = auto()
    USERS_HAVE_LAST_NAME = auto()
    USERS_HAVE_ORG_USERNAME = auto()

class ConfigGroupNames(str, Enum):
    """ Config settings are in groups to make the setting form more manageable """
    AUTH = "auth"
    GITHUB = "github"
    ORG = "org"
    PROJECT = "project"
    RACES = "races"
    SERVER = "server"
    SOCIAL = "social"
    TECH_NOTES = "tech_notes"
    USERS = "users"

class ConfigTypes(str, Enum):
    """ Explicit types of config settings (useful for validation, etc) """
    BOOLEAN = "bool"
    DATETIME = "datetime"
    INT = "int"
    PASSWORD = "pass"
    STRING = "str" # default TODO maybe ""?
    URL = "url"

class ConfigSettings:

    # Config settings prefixed with _ are not set by user, so do not appear
    # in GROUPS, which are used to present related settings together in the
    # admin/settings pages (otherwise it's overwhelming to manage).
    # If a setting isn't in a group here, the admin cannot change it through
    # the (web) admin/settings interface.

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
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name,
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
      ConfigGroupNames.RACES.name: (
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name,
      ),
      ConfigGroupNames.SERVER.name: (
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
        ConfigSettingNames.ADMIN_USERNAMES.name,
        ConfigSettingNames.AUTO_GENERATE_STATIC_CONTENT.name,
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name,
        ConfigSettingNames.SECRET_KEY.name,
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
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name,
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name,
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name,
        ConfigSettingNames.TASK_NAME_FOR_API.name,
        ConfigSettingNames.TASK_URLS_USE_ANCHORS.name,
        ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name,
      ),
      ConfigGroupNames.TECH_NOTES.name: (
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name,
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name,
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name,       
      )
    }


    # **Every** config setting in ConfigSettingNames **must** have an entry
    # in the DEFAULTS (it's used during setup to populate the database)

    DEFAULTS = {
        ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name: "buggyrace-issues.csv",
        ConfigSettingNames._ENV_SETTING_OVERRIDES.name: "",
        ConfigSettingNames._PUBLISHED_PATH.name: "published",
        ConfigSettingNames._SETUP_STATUS.name: 1, # by default, we're setting up!
        ConfigSettingNames._TECH_NOTES_PATH.name: "tech_notes",
        ConfigSettingNames._TECH_NOTES_CONTENT_DIR.name: "content",
        ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name: "tech_notes",
        ConfigSettingNames._TECH_NOTES_PAGES_DIR.name: "pages",
        ConfigSettingNames._TECH_NOTES_CONFIG_FILE_NAME.name: "pelicanconf.py",
        ConfigSettingNames._TECH_NOTES_CONFIG_LIVE_NAME.name: "pelicanconflive.py",
        ConfigSettingNames._TECH_NOTES_CONFIG_PUBLISH_NAME.name: "publishconf.py",
        ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name: "",
        ConfigSettingNames._TASK_LIST_HTML_FILENAME.name: "_task_list.html",
        ConfigSettingNames._TASKS_LOADED_DATETIME.name: "",
        ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name: "",
        ConfigSettingNames.ADMIN_USERNAMES.name: "",
        ConfigSettingNames.AUTHORISATION_CODE.name: bcrypt.generate_password_hash("CHANGEME").decode('utf8'),
        ConfigSettingNames.AUTO_GENERATE_STATIC_CONTENT.name: 0,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  "https://github.com/buggyrace/buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: "buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: "buggyrace",
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: "http://localhost:8000",
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: 200,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: 0,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: "",
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: 0,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: "",
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: "",
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: "Acme School of Buggy Programming",
        ConfigSettingNames.INSTITUTION_HOME_URL.name: "https://acme.example.com/",
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: "ASBP",
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name: 1,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: 0,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: 1,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: 0,
        ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name: 1,
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name: 1,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name: 0,
        ConfigSettingNames.PROJECT_CODE.name: "",
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name: 3,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name: "",
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name: "",
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: "report",
        ConfigSettingNames.PROJECT_SLUG.name: "",
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: "",
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: "",
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name: "",
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
        ConfigSettingNames.TASK_NAME_FOR_API.name: "5-API",
        ConfigSettingNames.TASK_URLS_USE_ANCHORS.name: 0,
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name: "",
        ConfigSettingNames.USERS_HAVE_EMAIL.name: 0,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: 0,
    }    
    
    MIN_PASSWORD_LENGTH = 4
    MIN_USERNAME_LENGTH = 2
    MAX_USERNAME_LENGTH = 32

    # TYPES are used to force casting when input either through the
    # admin/settings interface or simply when read as strings from ENV or the
    # database. By default they are strings, but it's best to be explicit.

    TYPES = {
        ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name: ConfigTypes.STRING,
        ConfigSettingNames._ENV_SETTING_OVERRIDES.name: ConfigTypes.STRING,
        ConfigSettingNames._PUBLISHED_PATH.name: ConfigTypes.STRING,
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
        ConfigSettingNames.ADMIN_USERNAMES.name: ConfigTypes.STRING,
        ConfigSettingNames.AUTHORISATION_CODE.name: ConfigTypes.PASSWORD,
        ConfigSettingNames.AUTO_GENERATE_STATIC_CONTENT.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  ConfigTypes.URL,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: ConfigTypes.URL,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: ConfigTypes.INT,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: ConfigTypes.STRING,
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_HOME_URL.name: ConfigTypes.URL,
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.PROJECT_CODE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name: ConfigTypes.INT,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SLUG.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: ConfigTypes.DATETIME,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: ConfigTypes.URL,
        ConfigSettingNames.PROJECT_WORKFLOW_URL.name: ConfigTypes.STRING,
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
        ConfigSettingNames.TASK_NAME_FOR_API.name: ConfigTypes.STRING,
        ConfigSettingNames.TASK_URLS_USE_ANCHORS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name: ConfigTypes.URL,
        ConfigSettingNames.USERS_HAVE_EMAIL.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: ConfigTypes.BOOLEAN,
    }

    # This is the order of the setting groups that is used during the
    # (initial) setup: the _SETUP_STATUS config is effectively the index-1
    # into this array: when the setup is complete, _SETUP_STATUS is zero.
    # (the settings page uses the same order, because it's sensible)
    SETUP_GROUPS = [
      ConfigGroupNames.AUTH,
      ConfigGroupNames.SERVER,
      ConfigGroupNames.ORG,
      ConfigGroupNames.SOCIAL,
      ConfigGroupNames.USERS,
      ConfigGroupNames.PROJECT,
      ConfigGroupNames.TECH_NOTES,
      ConfigGroupNames.RACES,
      ConfigGroupNames.GITHUB
    ]

    DESCRIPTIONS = {
        ConfigSettingNames.ADMIN_USERNAMES.name:
          """Comma separated list of admin user names. You can nominate usernames
          here before they have been registered. Usernames are lowercase.
          If you remove (or change) a username in this list, you're effectively
          revoking admin access, so **be careful** before changing anything.""",

        ConfigSettingNames.AUTHORISATION_CODE.name:
          """The authorisation code is needed to make any changes to config
          or other-user data, including registering students.
          See also `IS_PUBLIC_REGISTRATION_ALLOWED` for an exception.""",

        ConfigSettingNames.AUTO_GENERATE_STATIC_CONTENT.name:
          """The task list and tech notes do not get updated when you change
          config (or edit tasks): it's better to adopt the discipline of
          manually publishing both whenever you change config (which usally
          only happens  before project has started). If
          `AUTO_GENERATE_STATIC_CONTENT` is set, the race server will
          automatically republish the task list and the tech notes whenever
          it reboots. This might have an impact on the server's performance,
          and it's currently somewhat experimental. Only switch this on if
          you are experiencing problems with the build.""",

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

        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name:
          """Full ("base") URL of this server.""",

        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name:
          """The default point cost threshhold for buggies: you can always
          override this when you create each race.""",

        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name:
          """Should a race be public as soon as you create it? If you choose
          `No`, you'll have to remember to publish a race in order for students
          to see it.""",

        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name:
          """Races are grouped by league, so if you're using that mechanism you
          can nominate the league that new races are in here. It's common to
          run the race server without using leagues, so if you're not sure,
          leave this blank.""",

        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name:
          """Should the webserver itself force HTTPS? **Be careful**: this
          setting will not be helpful if your hosting environment manages
          this for you (that is, only set this to `Yes` if you are certain
          HTTPS requests arrive directly to the app: if you have a process
          that's handling requests and connecting with this app locally over
          HTTP, forcing redirects with this setting may prevent _any_ requests
          getting through). HTTPS is mandatory for GitHub's OAuth
          authentication, or if you're holding any personal information on
          students... but _this setting does not implement HTTPS_ — it only
          forces redirection if the protocol the app sees in incoming requests
          is (non-secure) HTTP.""",

        ConfigSettingNames.GITHUB_CLIENT_ID.name:
          """The GitHub client ID for the GitHub app that the server uses to
          fork the buggy editor repo into a student's own GitHub account.""",

        ConfigSettingNames.GITHUB_CLIENT_SECRET.name:
          """A string that exactly matches the client secret stored on the
          GitHub app that the server uses tofork the buggy editor repo into
          a student's own GitHub account.""",

        ConfigSettingNames.INSTITUTION_FULL_NAME.name:
          """Full name for your institution, college, or school.""",

        ConfigSettingNames.INSTITUTION_HOME_URL.name:
          """Full URL for the home page of your institution: used as a link
          on the racing server's home page.""",

        ConfigSettingNames.INSTITUTION_SHORT_NAME.name:
          """Short name or abbreviation for your institution, college,
          or school.""",

        ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name:
          """Choose `Yes` if all the config settings' values should be
          available when publishing tech notes. This setting is only
          relevant if you're customising the tech notes and/or publishing
          them externally. If `No`, only (sensible) selected config
          settings will be available as subtitutions in the tech notes'
          markdown. See the Pelican config file(s) for details.""",

        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name:
          """Should usernames (which are always lower case) be displayed using
          title case? For example, choose `Yes` if the usernames you're using
          are really students' names. Login is always case insensitive, so this
          only affects how usernames are displayed, not what users need to
          type.""",

        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name:
          """Typically, students are expected to submit their
          projects as a zip file containing the buggy editor web
          app (including a report/poster, if you've enabled it).
          The project page will display general information about
          those files (e.g., they should have the student's name
          just in case your submission process doesn't capture
          that: you end up with a lot of zip files with the same
          name otherwise). Use this setting to display or hide
          this general information on the "project" page.
          """,

        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name:
          """Can users register themselves? If not, only an admin user who
          knows the `AUTHORISATION_CODE` can register new users. Normally,
          the staff running the buggy racing project will register users so
          we strongly recommend public registration is not enabled.""",

        ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name:
          """Do you want students to be able to record notes on this server
          reporting they approached/did each task? If you're running
          the project with a report (see `PROJECT_REPORT_TYPE`), then this
          allows students to save notes here as they go along, which in
          turn gives you some visibility of their progress (which is why we
          implemented it). If you choose `No`, this feature will be hidden.
          Note that you _can_ choose `Yes`, letting students store task notes,
          even if the project doesn't require a report.""",

        ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name:
          """The admin interface normally lets you publish the tech
          notes, but if you're hosting them externally this might be
          confusing (because it certainly won't be changing your external
          site). However, there are circumstances where you want to be able
          to publish them here too, depending on how you're managing their
          creation. This setting doesn't affect the display of tech notes
          (see `TECH_NOTES_EXTERNAL_URL`), only whether the interface
          for publishing them is shown.""",

        ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name:
          """If your students will be using a remote server (see:
          `PROJECT_REMOTE_SERVER_NAME`) and are running VS Code over
          a remote session, the race server can produce a VS Code
          workspace file to facilitate cloning the repo onto that
          server and subequently acccess it through VS Code. This
          is quite a specific setup: if you're not sure, you almost
          certainly do not want this.
          """,

        ConfigSettingNames.PROJECT_CODE.name:
          """If this project is known by a course or module code, use it
          (for example, when we ran it at Royal Holloway, it was CS1999).
          See also `PROJECT_SLUG` which is how this code may appear in
          filenames of any downloaded files. The full name of the project
          is \"the `PROJECT_CODE` Racing Buggy project\", so if you don't
          have or need a course code, it's fine to leave it blank.""",

        ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name:
          """This is the minimum phase you'd expect an inexperienced
          programmer who's fully engaged in the project to have completed
          before running out of time. The default of 3 is based on our
          experience of running a 6-week project (several times) with
          students with only one term's prior experience of Python, and
          takes into account that task 3-MULTI is (deliberately) more
          involved than most students realise. This expectation is displayed
          to students (for example on the task list page). If you don't
          want this, set it to zero to remove the recommendation entirely.""",

        ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name:
          """If students are going to develop on a remote server,
          what is its address? This is used with their
          organisational username (or just username, if they haven't
          got one): for example enter `linux.example.ac.uk` so
          student Ada can log in via `ada@linux.example.ac.uk`.
          If you're not using a remote project server, leave this
          blank (see also `PROJECT_REMOTE_SERVER_NAME`).""",

        ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name:
          """If students are going to develop on a remote server,
          what is its (human-facing) name? This is used to help
          students identify the server they are logging into (e.g,
          "the CompSci department's Unix server").
          Leave this blank if your students are all working on their
          own machines (i.e., not a single teaching server with login
          accounts, python, and personalised HTTP ports).""",

        ConfigSettingNames.PROJECT_REPORT_TYPE.name:
          """If you require students to include a report of how
          they tackled the tasks, indicate that here ("report"
          or "poster" are just different names for the same thing,
          due to an historic anomaly). The report takes the form
          of an additional webpage in the student's buggy editor
          webserver. If you choose `No report`, all mentions will
          be removed: see also the `IS_STORING_STUDENT_TASK_NOTES`
          setting. """,

        ConfigSettingNames.PROJECT_SLUG.name:
          """This is how the `PROJECT_CODE` appears — as a prefix — in any
          filenames that are downloaded from the server. This is a kindness to
          help disambiguate files in your Downloads folder. If you leave this blank,
          it will default to using an automatic sluggified version of your project
          code, if any. Note that there are some places where students can download
          files (e.g., tabulated specification data) too, so it's not just admin
          staff who will see it.""",

        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name:
          """If you require all students to submit their projects
          on a specific deadline, set it here. This is displayed
          prominently (if the project is enabled) on the project
          page, but isn't currently used by the server for anything
          else. Avoid using 00:00 as a time because it confuses
          students — 23:59 is clearer (and 16:00 is healthier).
          Leave blank if you don't want to display a deadline at all
          (remember you can also use Announcements).""",

        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name:
          """Provide a link to either the web page where you'll
          be accepting submissions (presumably zip files) or
          else a page containing clear instructions for the
          students to follow. The buggy race server does
          not handle submissions itself. By default, no submission
          information is provided (because it's very dependent
          on each institution), which means no link is displayed:
          so you must supply one yourself.""",

        ConfigSettingNames.PROJECT_WORKFLOW_URL.name:
          """It's helpful for students to have a summary of the
          workflow process... but this often needs to be specific
          to how you're running your project — so you can nominate
          a URL to your own page. If the URL you specify here doesn't
          start with `http` (i.e., it's not a fully-qualified URL),
          it will default to `project/workflow` on this server. Leave
          this blank if you don't want to display a workflow page.""",

        ConfigSettingNames.SECRET_KEY.name:
          """A secret used by the webserver in cookies, etc. This should be unique
          for your server: the default value shown here was randomised on installation,
          so you usually don't need to change it. Note that changing it will
          almost certainly break existing sessions. For cleanest results, reboot
          the server as soon as you've changed it).""",

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

        ConfigSettingNames.TASK_NAME_FOR_API.name:
          """The name of the task (or tasks) that require use of the
          upload API. If set, this is shown as a helpful link in the
          explanotary text on the student's API settings page.
          If you set this to be empty, no link is show. You can provide
          mulitple task names by separating them with commas. If you
          haven't customised the task list, you don't need to change
          this.""",

        ConfigSettingNames.TASK_URLS_USE_ANCHORS.name:
          """By default, task URLs go direct to the server
          (e.g., `/project/tasks/3-multi`) and then redirect
          to an anchor within the page showing all tasks
          (e.g., `/project/tasks#task-3-multi`). This works fine
          on this server, and makes "nicer" URLs, but if you
          don't like this behaviour, switch it off.""",

        ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name:
          """Full URL to the tech notes pages if they are *not* being hosted
          on this server. If you've customised them and have published them
          somewhere else (for example, hosted on GitHub pages), then put the
          URL here. By default, tech notes are hosted on the race
          server, so you can leave this blank.""",

        ConfigSettingNames.USERS_HAVE_EMAIL.name:
          """Do users need email addresses? The server doesn't send emails so
          you don't need this field unless it's a useful way of identifying
          a student.""",

        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name:
          """Do users need to have a first name? You might be using each student's
          first name as the username, in which case you don't need this.""",

        ConfigSettingNames.USERS_HAVE_LAST_NAME.name:
          """Do users need to have a last name? If you can already identify your
          students from the other fields, you might not need this.""",

        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name:
          """Do users have a username or account that's specific to your
          organsiation or institution? You might not need this, or you
          might already be using it as the username — in which case
          choose `No`.""",

    }

    SETUP_GROUP_DESCRIPTIONS = {
      ConfigGroupNames.AUTH.name:
        """You must complete the setup. It takes around 5 minutes, and
        you can leave most settings to be default (and you can change
        most things later, if you need to).""",

      ConfigGroupNames.GITHUB.name:
        """Setup the GitHub details here. If you're injecting issues
        into student's own repos, you must provide valid GitHub
        CLIENT details which may be specific to your installation.""",

      ConfigGroupNames.ORG.name:
        """Provide general details about your institution/organisation.""",

      ConfigGroupNames.PROJECT.name:
        """These settings control aspects of the what the students
        need to do (for example: are they only coding, or do you
        want them to add a report/poster page to their buggy editor
        too?). If you or your department is running a remote server
        on which students will be doing their Python, enter its
        details here (there's extra set-up required on that remote
        server too — see the docs). It's fine to run the project
        without a remote server: it just means students work on
        individial machines.""",

      ConfigGroupNames.RACES.name:
        """Race settings can all be left to default (you can change them
        later if you need to).""",

      ConfigGroupNames.SERVER.name:
        """These settings control the behaviour of the server. The
        BUGGY_RACE_SERVER_URL setting is important; the others can
        usually be left to their default values.""",

      ConfigGroupNames.SOCIAL.name:
        """These are used to add links to your institution's social or
        educational accounts. If you run support sites like Moodle
        or Discord or Teams for this project, add them here.""",

      ConfigGroupNames.TECH_NOTES.name:
        """The tech notes are static webpages with supporting or
        explanatory material specific to the project, and even some
        tasks. You cannot customise them on this server (i.e.,
        through this web interface) but you can host them externally
        (e.g., on your own course website or GitHub pages), in which
        case set the external URL here. For details on how to extract
        the tech notes for self-publication, see separate docs.""",

      ConfigGroupNames.USERS.name:
        """Every student will need a username. These settings define what
        fields you want to store IN ADDITION to that username. You do
        not need to have any additional fields (we recommend you only
        add them if you really need to, for example, if the usernames
        aren't already the students' first names, maybe add a first
        name so you can recognise who they are). Only admin users see
        these additional fields — they aren't made public.""",
    }

    NO_KEY = "_NOTHING_" # special case of unexpected config with no key

    UNEXPECTED_SETTINGS_KEY = "_UNEXPECTED_CONFIG_SETTINGS"

    @staticmethod
    def is_valid_name(name):
      return name in ConfigSettings.DEFAULTS
  
    @staticmethod
    def prettify(name, value):
      if ConfigSettings.TYPES.get(name) == ConfigTypes.BOOLEAN:
        return "No" if (value == "0" or not bool(value)) else "Yes"
      return value

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
      if type == ConfigTypes.PASSWORD:
        str_value = None
      elif type is None or type in (
         ConfigTypes.DATETIME,
         ConfigTypes.STRING,
         ConfigTypes.URL,
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
        app.config[name] = value

    @staticmethod
    def admin_usernames_list(app):
        admin_users_str = app.config.get(ConfigSettingNames.ADMIN_USERNAMES.name)
        if admin_users_str is None:
          return []
        else:
          return [user.strip() for user in admin_users_str.split(",")]
    
    @staticmethod
    def users_additional_fieldnames_is_enabled_dict(app):
        return {
            "email": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_EMAIL.name)
            ),
            "org_username": bool(
              app.config.get(ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name)
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


##################################################################

env = Env()
env.read_env()

class ConfigFromEnv():

    # set up phase:
    # 0 - all done! (admin has full access to settings)
    # 1 - force change of auth code, get admin username and password
    # 2+ - subsquent settings (broken down into groups)
    _SETUP_STATUS = env.str(str(ConfigSettingNames._SETUP_STATUS), default=None)

    # some (not-buggy-race-specific) config _only_ comes from the ENV
    FLASK_APP = env.str("FLASK_APP", default="autoapp.py")
    FLASK_ENV = env.str("FLASK_ENV", default="production")
    FLASK_DEBUG = DEBUG = FLASK_ENV == "development"

    UPLOAD_FOLDER = "buggy_race_server/uploads"

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
      # By putting the env names into _ENV_SETTING_OVERRIDES, the settings
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
      self._ENV_SETTING_OVERRIDES = ",".join(env_setting_overrides)
