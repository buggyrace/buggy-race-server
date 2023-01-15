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

    # settings prefixed by _ are implied, so should not be set explicitly

    # current announcements are cached to avoid database reads on every hit
    _CURRENT_ANNOUNCEMENTS="_CURRENT_ANNOUNCEMENTS"

    # setup status is used to track progress (and ultimately completion)
    # of the setup process when the app is first installed
    _SETUP_STATUS="_SETUP_STATUS"

    # settings that are being overridden by ENV variables (by this
    # class) are noted here so a warning can be displayed on the settings page
    _ENV_SETTING_OVERRIDES="_ENV_SETTING_OVERRIDES"

    # tech notes are managed by Pelcian: we don't anticipate the tech notes
    # dir being changed (it's in version control) so they aren't offered via
    # admin/settings... but just in case, putting them in config to allow
    # future tech notes to come from a different source: defaults values
    # are set in ConfigFromEnv, below
    TECH_NOTES_PATH="TECH_NOTES_PATH"
    TECH_NOTES_OUTPUT_PATH="TECH_NOTES_OUTPUT_PATH"
    TECH_NOTES_PAGES_PATH="TECH_NOTES_PAGES_PATH"


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
    IS_PROJECT_ZIP_INFO_DISPLAYED="IS_PROJECT_ZIP_INFO_DISPLAYED"
    IS_PUBLIC_REGISTRATION_ALLOWED="IS_PUBLIC_REGISTRATION_ALLOWED"
    PROJECT_REPORT_TYPE="PROJECT_REPORT_TYPE"
    PROJECT_CODE="PROJECT_CODE"
    PROJECT_SLUG="PROJECT_SLUG"
    PROJECT_SUBMISSION_DEADLINE="PROJECT_SUBMISSION_DEADLINE"
    PROJECT_SUBMISSION_LINK="PROJECT_SUBMISSION_LINK"
    REGISTRATION_AUTH_CODE="REGISTRATION_AUTH_CODE"
    SECRET_KEY="SECRET_KEY"
    SERVER_PROJECT_PAGE_PATH="SERVER_PROJECT_PAGE_PATH"
    SOCIAL_0_NAME="SOCIAL_0_NAME"
    SOCIAL_0_TEXT="SOCIAL_0_TEXT"
    SOCIAL_0_URL="SOCIAL_0_URL"
    SOCIAL_1_NAME="SOCIAL_1_NAME"
    SOCIAL_1_TEXT="SOCIAL_1_TEXT"
    SOCIAL_1_URL="SOCIAL_1_URL"
    SOCIAL_2_NAME="SOCIAL_2_NAME"
    SOCIAL_2_TEXT="SOCIAL_2_TEXT"
    SOCIAL_2_URL="SOCIAL_2_URL"
    SOCIAL_3_NAME="SOCIAL_3_NAME"
    SOCIAL_3_TEXT="SOCIAL_3_TEXT"
    SOCIAL_3_URL="SOCIAL_3_URL"
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
    PROJECT = "project"
    RACES = "races"
    SERVER = "server"
    SOCIAL = "social"

class ConfigTypes(str, Enum):
    """ Explicit types of config settings (useful for validation, etc) """
    STRING = "str" # default TODO maybe ""?
    BOOLEAN = "bool"
    DATETIME = "datetime"
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
      },
      ConfigGroupNames.PROJECT.name: {
        ConfigSettingNames.PROJECT_REPORT_TYPE.name,
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name,
        ConfigSettingNames.PROJECT_CODE.name,
        ConfigSettingNames.PROJECT_SLUG.name,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name,
      }
    }
    DEFAULTS = {
        ConfigSettingNames._SETUP_STATUS.name: 1, # by default, we're setting up
        ConfigSettingNames.ADMIN_USERNAMES.name: "",
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  "https://github.com/buggyrace/buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name: "buggyrace-issues.csv",
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: "buggy-race-editor",
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: "buggyrace",
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: "http://localhost:8000",
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: 200,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: 0,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: "",
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: 0,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: "",
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: "",
        ConfigSettingNames.GITHUB_PAGES_URL.name: "",
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: "Acme School of Buggy Programming",
        ConfigSettingNames.INSTITUTION_HOME_URL.name: "https://acme.example.com/",
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: "ASBP",
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: 0,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: 1,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: 0,
        ConfigSettingNames.PROJECT_CODE.name: "Buggy",
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: "report",
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: "",
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: "",
        ConfigSettingNames.PROJECT_SLUG.name: "",
        ConfigSettingNames.REGISTRATION_AUTH_CODE.name: "CHANGEME",
        ConfigSettingNames.SECRET_KEY.name: f"{randint(10000, 99999)}-secret-{randint(10000, 99999)}",
        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name: "project",
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
        ConfigSettingNames.USERS_HAVE_EMAIL.name: 0,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: 0,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: 0,
    }    
    
    MIN_PASSWORD_LENGTH = 4
    MIN_USERNAME_LENGTH = 2
    MAX_USERNAME_LENGTH = 32

    TYPES = {
        ConfigSettingNames._SETUP_STATUS.name: ConfigTypes.INT,
        ConfigSettingNames.ADMIN_USERNAMES.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name:  ConfigTypes.URL,
        ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name: ConfigTypes.STRING,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name: ConfigTypes.URL,
        ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name: ConfigTypes.INT,
        ConfigSettingNames.DEFAULT_RACE_IS_VISIBLE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.DEFAULT_RACE_LEAGUE.name: ConfigTypes.STRING,
        ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.GITHUB_CLIENT_ID.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_CLIENT_SECRET.name: ConfigTypes.STRING,
        ConfigSettingNames.GITHUB_PAGES_URL.name: ConfigTypes.URL,
        ConfigSettingNames.INSTITUTION_FULL_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.INSTITUTION_HOME_URL.name: ConfigTypes.URL,
        ConfigSettingNames.INSTITUTION_SHORT_NAME.name: ConfigTypes.STRING,
        ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.PROJECT_CODE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_REPORT_TYPE.name: ConfigTypes.STRING,
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name: ConfigTypes.DATETIME,
        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name: ConfigTypes.URL,
        ConfigSettingNames.PROJECT_SLUG.name: ConfigTypes.STRING,
        ConfigSettingNames.REGISTRATION_AUTH_CODE.name: ConfigTypes.PASSWORD,
        ConfigSettingNames.SECRET_KEY.name: ConfigTypes.STRING,
        ConfigSettingNames.SERVER_PROJECT_PAGE_PATH.name: ConfigTypes.STRING,
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
        ConfigSettingNames.USERS_HAVE_EMAIL.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_FIRST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_LAST_NAME.name: ConfigTypes.BOOLEAN,
        ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name: ConfigTypes.BOOLEAN,
    }

    # this is the order of the setting groups that is
    # used during the (initial) setup: the _SETUP_STATUS
    # config is effectively the index-1 into this array:
    # when the setup is complete, _SETUP_STATUS is zero.
    # (the settings page uses the same order, because it's sensible)
    SETUP_GROUPS = [
      ConfigGroupNames.AUTH,
      ConfigGroupNames.SERVER,
      ConfigGroupNames.ORG,
      ConfigGroupNames.SOCIAL,
      ConfigGroupNames.USERS,
      ConfigGroupNames.PROJECT,
      ConfigGroupNames.RACES,
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
          so you usually don't need to change it. Note that changing it will
          almost certainly break existing sessions.""",

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

        ConfigSettingNames.REGISTRATION_AUTH_CODE.name:
          """The authorisation code is needed to make any changes to user data,
          including registering students. If `IS_PUBLIC_REGISTRATION_ALLOWED`
          is 'Yes' then anyone can register a single user (not recommended).""",

        ConfigSettingNames.ADMIN_USERNAMES.name:
          """Comma separated list of admin user names. You can nominate usernames
          here before they have been registered. Usernames are lowercase.
          If you remove (or change) a username in this list, you're effectively
          revoking admin access, so be careful before changing anything.""",

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
          public registration should not be enabled.""",

        ConfigSettingNames.PROJECT_REPORT_TYPE.name:
          """If you require students to include a report of how
          they tackled the tasks, indicate that here ("report"
          or "poster" are just different names for the same thing,
          due to an historic anomaly). The report takes the form
          of an additional webpage in the student's buggy editor
          webserver.""",
        
        ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name:
          """If you require all students to submit their projects
          on a specific deadline, set it here. This is displayed
          prominently (if the project is enabled) on the project
          page, but isn't currently used by the server for anything
          else. Avoid the 00:00 as a time because it confuses
          students (23:59 is clearer, and 16:00 healthier).
          Leave blank if you don't want to display a deadline at all
          (remember you can also use Announcements).
          """,

        ConfigSettingNames.PROJECT_SUBMISSION_LINK.name:
          """Provide a link to either the web page where you'll
          be accepting submissions (presumably zip files) or
          else a page containing clear instructions for the
          students to follow. The buggy race server does
          not handle submissions itself. By default, no submission
          information is provided (because it's very dependent
          on each institution), which means no link is displayed:
          so you must supply one yourself.
          """,

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
          """
    }

    SETUP_GROUP_DESCRIPTIONS = {
      ConfigGroupNames.AUTH.name:
        """
        You must complete the setup. It takes around 5 minutes, and
        you can leave most settings to be default (and you can change
        most things later, if you need to).
        """,
      ConfigGroupNames.ORG.name:
        """
        Provide general details about your institution/organisation.
        """,
      ConfigGroupNames.USERS.name:
        """
        Every student will need a username. These settings define what
        fields you want to store IN ADDITION to that username. You do
        not need to have any additional fields (we recommend you only
        add them if you really need to, for example, if the usernames
        aren't already the students' first names, maybe add a first
        name so you can recognise who they are). Only admin users see
        these additional fields — they aren't made public.
        """,
      ConfigGroupNames.SERVER.name:
        """
        These settings control the behaviour of the server. The
        BUGGY_RACE_SERVER_URL setting is important; the others can
        usually be left to their default values.
        """,
      ConfigGroupNames.RACES.name:
        """
        Race settings can all be left to default (you can change them
        later if you need to).
        """,
      ConfigGroupNames.SOCIAL.name:
        """
        These are used to add links to your institution's social or
        educational accounts. If you run support sites like Moodle
        or Discord or Teams for this project, add them here.
        """,
      ConfigGroupNames.GITHUB.name:
        """
        Setup the GitHub details here. If you're injecting issues
        into student's own repos, you must provide valid GitHub
        CLIENT details which may be specific to your installation.
        """,
      ConfigGroupNames.PROJECT.name:
        """
        These settings control aspects of the what the students
        need to do (for example: are they only coding, or do you
        want them to add a report/poster page to their buggy editor
        too?).
        """

    }

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
      if ConfigSettings.TYPES.get(name) == ConfigTypes.BOOLEAN:
        return "1" if value else "0"
      return str(value)

    @staticmethod
    def set_config_value(app, name, value):
        """ Sets config value in the app (casting to correct type)
            Note: this does NOT do anything with the database!
        """
        str_value = str(value)
        type = ConfigSettings.TYPES[name]
        if type == ConfigTypes.BOOLEAN:
            value = str_value == "1"
        elif type == ConfigTypes.INT:
            value = int(str_value) if str_value.isdecimal() else 0
        app.config[name] = value
        print(f"* updated config value: {name}={value}", flush=True)

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
            "email": bool(app.config.get(ConfigSettingNames.USERS_HAVE_EMAIL.name)),
            "org_username": bool(app.config.get(ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name)),
            "first_name": bool(app.config.get(ConfigSettingNames.USERS_HAVE_FIRST_NAME.name)),
            "last_name": bool(app.config.get(ConfigSettingNames.USERS_HAVE_LAST_NAME.name)),
        }

    @staticmethod
    def users_additional_fieldnames(app):
        is_enabled_dict = ConfigSettings.users_additional_fieldnames_is_enabled_dict(app)
        return [ field for field in is_enabled_dict if is_enabled_dict[field] ]

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

    # string containing comma separated config setting names that are
    # stored in database but have been overridden by ENV settings
    # (see constructor below)
    _ENV_SETTING_OVERRIDES = ""

    # hardcoded settings for Pelican (python tool for static site generation):
    # These only need to be changed if you're not using tech notes from this
    # repo, which currently isn't supported. Because these are reading raw
    # files from the filesystem and serving them to the client, there's a
    # security risk if they point anywhere outside the repo... which is
    # why they aren't offered for changing via the admin/settings pages.
    #------------------------------------------------------------------
    # the "Pelican" directory (contains source and config for generating tech notes static content)
    TECH_NOTES_PATH= env.str("TECH_NOTES_PATH", default="../tech_notes")
    # the output directory of the tech notes, specifically the pages (because Pelican wants
    # to generate other material — blog posts, summaries — which we're not using)
    TECH_NOTES_OUTPUT_PATH= env.str("TECH_NOTES_OUTPUT_PATH", default="../tech_notes/output")
    # the HTML pages themselves (pages subdir in the output path)
    TECH_NOTES_PAGES_PATH= env.str("TECH_NOTES_PAGES_PATH", default=f"{TECH_NOTES_OUTPUT_PATH}/pages") 

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
          if env.str(name, default=None):
              setattr(self, name, env.str(name))
              env_setting_overrides.append(name)
      self._ENV_SETTING_OVERRIDES = ",".join(env_setting_overrides)
