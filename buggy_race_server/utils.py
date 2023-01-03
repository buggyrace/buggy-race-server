# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request, redirect, Markup, url_for, current_app
from wtforms import ValidationError
from functools import wraps
from flask_login import current_user, logout_user
from buggy_race_server.config import ConfigSettingNames
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

def is_authorised(form, field):
  """ check the auth code — required for some admin activities (mainly user registration)"""
  auth_code = current_app.config.get(ConfigSettingNames.REGISTRATION_AUTH_CODE)
  if auth_code is None:
    raise ValidationError("No authorisation code has been set: cannot authorise")
  if field.data != auth_code:
    raise ValidationError(f"You must provide a valid authorisation code")
  return True

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

def save_config_env_overrides_to_db(app):
    """ Saves each config setting that's in the app config into the database.
      This is specifically used when the app starts up, to save any settings
      that are being set by environment variables in the database _before_
      the app then loads the entire config — including defaults — back from
      the database. This mechanism allows ENV overriding of bad/broken config.
    """
    if names := app.config.get(ConfigSettingNames._ENV_SETTING_OVERRIDES):
      for name in names.split(","):
        value = app.config.get(name) # expecting a value here
        if value is not None:
          set_and_save_config_setting(app, name, value)
          print(f"* written {name} config setting (from ENV) into database", flush=True)

def load_settings_from_db(app):
    """ Read settings from db and set the app's config appropriately."""
    settings = Setting.query.all()
    is_config_set = { name: False for name in ConfigSettings.DEFAULTS }
    for setting in settings:
        name = setting.id
        if name in ConfigSettings.DEFAULTS: # it's an expected config name
            ConfigSettings.set_config_value(app, setting.id, setting.value)
            is_config_set[name] = True
        else:
            print(f"[ ] found an unexpected config setting name \"{name}\" in the db, ignored")
    missing_settings = [
        {
          "id": name,
          "value": ConfigSettings.stringify(
              name,
              ConfigSettings.DEFAULTS[name]
          )
        }
        for name in is_config_set if not is_config_set[name]
    ]
    if missing_settings:
      db.session.execute(insert(Setting.__table__), missing_settings)
      db.session.commit()
    print(f"* inserted {len(missing_settings)} config settings (with default values) into database", flush=True)

def set_and_save_config_setting(app, name, value):
    # this changes the app's config setting and also saves that
    # change in the database.
    # This isn't used much because the admin settings page (the
    # way settings are usually changed) uses bulk updates because
    # the forms handle groups of settings.
    app.config[name]=value
    # could check that name is a valid config key?
    setting = Setting.query.filter_by(id=name).first()
    if setting is None: # not already in db? then make it
        setting = Setting.create(id=name, value=value)
    else:
        setting.value = value
    setting.save()
  
def prettify_form_field_name(name):
  """ for flash error messages (e.g., 'auth_code' become 'Auth Code') """
  return name.replace("_", " ").title()