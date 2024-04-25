# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys
from datetime import datetime, timezone
from sqlalchemy.exc import OperationalError
from os import path
import re

#import traceback # for debug/dev work

from flask import Flask, make_response, render_template, request, redirect, url_for, session
from flask_login import current_user

from buggy_race_server import admin, api, buggy, commands, config, oauth, public, race, user
from buggy_race_server.utils import (
    create_editor_zipfile,
    refresh_global_announcements,
    publish_tasks_as_issues_csv,
    publish_task_list,
    publish_tech_notes,
    save_config_env_overrides_to_db,
    load_settings_from_db,
    servertime_str,
    join_to_project_root,
    has_settings_table,
)
from buggy_race_server.admin.models import Announcement
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
from buggy_race_server.extensions import (
    bcrypt,
    cache,
    csrf,
    db,
    debug_toolbar,
    flask_static_digest,
    login_manager,
    migrate,
)

def create_app():
    """Create application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/
    See config.py which loads config from env vars:
    specify all non-defaulted settings with environment variables
    (either using .env or explicit exports/settings (e.g., via Heroku's dialogue))
    ...but access them through the Flask's app.config['KEY_NAME']
    """

    app = Flask(__name__.split(".")[0])

    app.config.from_object(config.ConfigFromEnv())

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    configure_logger(app)

    csrf.exempt(app.blueprints['api'])

    # Flask's db migration needs to instantiate the app even though the
    # database has not been initialised yet.

    with app.app_context():
        try:
            if has_settings_table():
                # settings/config table exists in database so migrations
                # have probably been applied, and everything is OK
                save_config_env_overrides_to_db(app)
                load_settings_from_db(app)
                refresh_global_announcements(app)
            else:
                print("[!] WARNING: missing settings/config table: " +
                  "app had unpopulated database when created", file=sys.stderr)
                # this is catastrophic *unless* this is a Flask db operation...
                # ...in which case it's trying to populate it, return 
                if (
                    sys.argv[0].endswith("flask") and 
                    len(sys.argv) > 1 and sys.argv[1]=="db"
                ):
                    print("[ ] but that's probably OK because this is a flask db operation", file=sys.stderr)
                # set initi config message in case this continues to run as
                # a webserver (if this was a flask migration, it won't be)
                app.config['INIT_ERROR_MESSAGE'] = """Warning: app had unpopulated database (missing table): 
                  need to run migrations first, or schema.sql?"""

        except OperationalError as e:
            print(f"* ERROR: database problem: {e}", file=sys.stderr)
            app.config['INIT_ERROR_MESSAGE'] = """Database error — probably
              a failure to connect: check DATABASE_URL and error logs"""

    # must register any jinja filters before rendering any static content
    def get_servertime(utc_datetime):
        return servertime_str(
            app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
            utc_datetime
        )
    def get_servertime_age_in_s(utc_datetime):
        if utc_datetime:
            if type(utc_datetime) == str:
                if m := re.search(
                    "\s*(\d\d\d\d-\d\d-\d\d \d\d:\d\d)(:\d\d)?.*",
                    utc_datetime
                ):
                    m = m.groups()
                    utc_datetime = datetime.strptime(
                        f"{m[0]}{m[1] or ':00'}", "%Y-%m-%d %H:%M:%S"
                    ).astimezone(timezone.utc)
            if type(utc_datetime) == datetime:
                diff = datetime.now(timezone.utc) - utc_datetime
                return int(diff.total_seconds())
 
    app.jinja_env.filters['servertime'] = get_servertime
    app.jinja_env.filters['servertime_age_in_s'] = get_servertime_age_in_s

    if app.config.get(ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name):
        # the very first time this runs, server URL might not be set...
        # ...but that's OK because the task list is probably empty too
        server_url = app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]

        with app.test_request_context(server_url):

            if app.config.get(ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name):
                generated_task_file = join_to_project_root(
                    app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                    app.config[ConfigSettingNames._TASK_LIST_HTML_FILENAME.name]
                )
                if not path.exists(generated_task_file):
                    print(f"* publishing task list (for {server_url})", flush=True)
                    publish_task_list(app)
                    print(f"* published task list", flush=True)

                generated_issue_file = join_to_project_root(
                    app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                    app.config[ConfigSettingNames._BUGGY_EDITOR_ISSUES_CSV_FILE.name]
                )
                if not path.exists(generated_issue_file):
                    publish_tasks_as_issues_csv(app)
                    print(f"* published task issues CSV", flush=True)

            if app.config.get(ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name):
                tech_notes_sample_file = join_to_project_root(
                    app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                    app.config[ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name],
                    app.config[ConfigSettingNames._TECH_NOTES_PAGES_DIR.name],
                    "index.html"
                )
                if not path.exists(tech_notes_sample_file):
                    print(f"* publishing tech notes (for {server_url})", flush=True)
                    publish_tech_notes(app)
                    print(f"* published tech notes", flush=True)

            if (
                app.config.get(ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name)
                and not app.config.get(ConfigSettingNames.IS_USING_GITHUB.name)
            ):
                target_zipfile = join_to_project_root(
                    app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                    app.config[ConfigSettingNames._EDITOR_OUTPUT_DIR.name],
                    app.config[ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name]
                )
                if not path.exists(target_zipfile):
                    print(f"* publishing buggy editor zipfile", flush=True)
                    create_editor_zipfile(None, app=app)
                    print(f"* published buggy editor zipfile", flush=True)

    @app.before_request
    def force_setup_on_new_installs():
        """ Prevent access to any pages other than setup or login.
            Access to login is also allowed, since an interrupted setup can
            continue by logging in with an admin account."""
        setup_status = app.config.get(ConfigSettingNames._SETUP_STATUS.name)
        if not (setup_status is None or request.path.startswith(app.static_url_path)):
            try:
                if int(setup_status) > 0:
                    setup_url = url_for("admin.setup")
                    if not (request.path == setup_url or request.path == url_for("public.login")):
                        return redirect(f"{request.root_path}{setup_url}")
            except ValueError:
                pass # ignore unexpected bad setup value, and allow access

    if app.config.get(ConfigSettingNames.IS_REDIRECT_HTTP_TO_HTTPS_FORCED.name):
        @app.before_request
        def force_redirect_http_to_https():
            if not request.is_secure:
                return redirect(request.url.replace('http://', 'https://', 1), code=301)

    @app.before_request
    def bump_login_timestamp():
        ACTIVITY_AT = "activity_at"
        activity_update_period_s = app.config.get(ConfigSettingNames.USER_ACTVITY_PERIOD_S.name) or 0
        if current_user and current_user.is_authenticated and session:
            now_utc = datetime.now(timezone.utc)
            active_timestamp = session.get(ACTIVITY_AT)
            if not active_timestamp:
                active_timestamp = session[ACTIVITY_AT] = now_utc
                delta_s = 0
            else:
                try:
                    delta_s = (now_utc - active_timestamp).total_seconds()
                except TypeError as e: # login timestamp wasn't UTC
                    current_user.logged_in_at = now_utc
                    current_user.save()
                    delta_s = 0
            if delta_s and delta_s > activity_update_period_s:
                current_user.logged_in_at = now_utc
                current_user.save()
                active_timestamp = session[ACTIVITY_AT] = now_utc

    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(admin.views.blueprint)
    app.register_blueprint(admin.views_races.blueprint)
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(buggy.views.blueprint)
    app.register_blueprint(api.views.blueprint)
    app.register_blueprint(oauth.views.blueprint)
    app.register_blueprint(race.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        response = make_response(
            render_template(f"{error_code}.html", error=error), error_code
        )
        # werkzeug.exceptions.MethodNotAllowed has a valid_methods list,
        # but Flask doesn't add the Allow: header the HTTP spec says it should
        # https://httpwg.org/specs/rfc9110.html#status.405
        if error_code == 405 and error.valid_methods:
            response.headers.set("Allow", ", ".join(error.valid_methods))
        return response

    for errcode in [400, 401, 403, 404, 405, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, 
            "User": user.models.User,
            "Buggy": buggy.models.Buggy,
            "Race": race.models.Race
          }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)


# Instead of having gunicorn call the create_app function as the entry point,
# we just need to allow this Python file to run, create the app (WSGI callable)
# and the app context, ORM etc are all established.
# Decorators now start to work too, and here seems the best place to put them.
app = create_app()
