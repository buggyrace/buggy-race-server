# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys

#import traceback # for debug/dev work

from flask import Flask, render_template, request, redirect, url_for

from buggy_race_server import admin, api, buggy, commands, config, oauth, public, race, user
from buggy_race_server.utils import (
    refresh_global_announcements,
    publish_task_list,
    publish_tech_notes,
    save_config_env_overrides_to_db,
    load_settings_from_db
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
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.
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

    with app.app_context():

        save_config_env_overrides_to_db(app)
        load_settings_from_db(app)
        refresh_global_announcements(app)

    if app.config[ConfigSettingNames.AUTO_GENERATE_STATIC_CONTENT.name]:
        # the very first time this runs, server URL might not be set...
        # ...but that's OK because the task list is probably empty too
        server_url = app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
        with app.test_request_context(server_url):
            print(f"* publishing task list (for {server_url})", flush=True)
            publish_task_list(app)
            print(f"* published task list", flush=True)
        
            print(f"* publishing tech notes (for {server_url})", flush=True)
            publish_tech_notes(app)
            print(f"* published tech notes", flush=True)

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

    if app.config.get(ConfigSettingNames.FORCE_REDIRECT_HTTP_TO_HTTPS.name):
        @app.before_request
        def force_redirect_http_to_https():
            if not request.is_secure:
                return redirect(request.url.replace('http://', 'https://', 1), code=301)

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
        return render_template(f"{error_code}.html"), error_code

    for errcode in [400, 401, 403, 404, 500]:
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
