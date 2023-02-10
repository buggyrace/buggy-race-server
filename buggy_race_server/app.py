# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys

#import traceback # for debug/dev work

from flask import Flask, render_template

from buggy_race_server import admin, api, buggy, commands, config, oauth, public, race, user
from buggy_race_server.utils import (
    refresh_global_announcements,
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

        try:
            save_config_env_overrides_to_db(app)
            settings_dict = load_settings_from_db(app)
        except Exception as e:
            #traceback.print_exception(type(e), e, e.__traceback__)
            print(f"init error: {e}")
            return app # no more work: allows flask db init, etc

        try:
            qty_announcements = Announcement.query.count()
        except Exception as e:
            print(f"init error: {e}")
            return app # no more work: allows flask db init, etc

        if qty_announcements == 0:
            # note: this is *not* publishing an announcement, it's seeding an example
            Announcement.create(
                type="special",
                text=Announcement.EXAMPLE_ANNOUNCEMENT,
                is_html=True,
                is_visible=False,
            )
        # and now load any published (is_visible=True) announcements into the config
        refresh_global_announcements(app)

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
