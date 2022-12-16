# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request, redirect, Markup, url_for, current_app
from wtforms import ValidationError
from functools import wraps
from flask_login import current_user, logout_user
from buggy_race_server.config import ConfigFromEnv
from buggy_race_server.admin.models import Announcement, Setting, ConfigSettings
from buggy_race_server.extensions import db
from sqlalchemy import insert

def refresh_global_announcements(app):
  app.config['CURRENT_ANNOUNCEMENTS'] = Announcement.query.filter_by(is_visible=True)

def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)

def warn_if_insecure():
  pass # TODO delegating this to (Cloudflare) host/DNS config, not application level

def flash_suggest_if_not_yet_githubbed(function):
  @wraps(function)
  def wrapper():
    if current_user and not current_user.is_github_connected():
      flash(Markup(f"You haven't connected to GitHub yet. <a href='{url_for('user.settings')}'>Do it now!</a>"), "danger")
    return function()
  return wrapper

# prevent unauthorised registration if there is an auth code in the environment
def is_authorised(form, field):
  auth_code = current_app.config[ConfigSettings.REGISTRATION_AUTH_CODE]
  if auth_code is not None and field.data.lower() != auth_code.lower():
    raise ValidationError("You must provide a valid authorisation code")

# check current user is active: this catches (and logs out) a user who has been
# made inactive _during_ their session: need this so admin can (if needed) bump
# students off the server (even if they are currently logged in). An inactive
# user can't log back in (because login rejects attempts by inactive usernames).
def active_user_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user and not current_user.is_active:
            flash(f"User \"{current_user.username}\" is inactive", "danger")
            logout_user()
            return redirect(url_for("public.home"))
        return function(*args, **kwargs)
    return wrapper

def insert_default_settings_into_db(app):
    db.session.execute(
        insert(Setting.__table__),
        [
            {"id": name, "value": ConfigSettings.DEFAULTS[name]}
            for name in ConfigSettings.DEFAULTS
        ]
    )
    db.session.commit()
    print(f"*** loaded {len(ConfigSettings.DEFAULTS)} config settings into database with default values", flush=True)

def load_settings_from_db(app):
    settings = Setting.query.all()
    if len(settings) == 0:
        insert_default_settings_into_db(app)
        settings = Setting.query.all()

    for setting in settings:
        name = setting.id
        if name in ConfigSettings.DEFAULTS:
            ConfigSettings.set_config_value(app, setting.id, setting.value)
        else:
            pass # not in defaults (unexpected setting?) TODO
    
    ConfigSettings.imply_extra_settings(app)