# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
import os # for path
import re
from flask import flash, request, redirect, Markup, url_for, current_app
from wtforms import ValidationError
from functools import wraps
from flask_login import current_user, logout_user
from buggy_race_server.config import ConfigSettingNames, ConfigSettings
from buggy_race_server.admin.models import Announcement, Setting
from buggy_race_server.extensions import db
from sqlalchemy import bindparam, insert, update
from datetime import datetime

import subprocess

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
  auth_code = current_app.config.get(ConfigSettingNames.REGISTRATION_AUTH_CODE.name)
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
    if names := app.config.get(ConfigSettingNames._ENV_SETTING_OVERRIDES.name):
      for name in names.split(","):
        value = app.config.get(name) # expecting a value here
        if value is not None:
          set_and_save_config_setting(app, name, value)
          print(f"* written {name} config setting (from ENV) into database", flush=True)

def load_settings_from_db(app):
    """ Read settings from db and set the app's config appropriately.
        This is inefficient — we hit the database more than once — but it's only called
        during app startup, setup, or when settings are being explicitly changed.

        Note that, at startup, if there are ENV variables set for any config,
        those are written to the database _before_ this, which is how they 
        always override (and why we don't care if they are already set).
    """
    settings = Setting.query.all()
    names_found_in_db = [setting.id for setting in settings if ConfigSettings.is_valid_name(setting.id)]
    missing_settings = []
    for name in ConfigSettings.DEFAULTS.keys():
       if name not in names_found_in_db:
          # explicitly write the default value into the db for missing settings
          # This is only expected when the app first starts up: after that, the
          # config settings remain in the database
          missing_settings.append(
            {
              "id": name,
              "value": ConfigSettings.stringify(name, ConfigSettings.DEFAULTS[name])
            }
          )
    if missing_settings:
        db.session.execute(insert(Setting.__table__), missing_settings)
        db.session.commit()
        print(f"* inserted {len(missing_settings)} config settings (with default values) into database", flush=True)
        # now reload settings: this time it won't have any missing
        settings = Setting.query.all()

    for setting in settings:
        # set_config_value casts to correct type (e.g., bool/int/str)
        ConfigSettings.set_config_value(app, setting.id, setting.value)

    return Setting.get_dict_from_db(settings) # pass the settings back as a dict


def set_and_save_config_setting(app, name, value):
    # this changes the app's config setting and also saves that
    # change in the database.
    # This isn't used much because the admin settings page (the
    # way settings are usually changed) uses bulk updates because
    # the forms handle groups of settings.

    ConfigSettings.set_config_value(app, name, value)
    setting = db.session.query(Setting).filter_by(id=name).first()
    settings_table = Setting.__table__
    if setting is None: # not already in db? then make it
        db.session.execute(
          insert(settings_table),
          [ {"id": name, "value": value} ]
        )
    else:
        db.session.execute(
          update(settings_table)
            .where(settings_table.c.id == bindparam("name"))
            .values(value=bindparam("value")),
            [ {"name": name, "value": value} ]
        )
    db.session.commit()
  
def prettify_form_field_name(name):
  """ for flash error messages (e.g., 'auth_code' become 'Auth Code') """
  return name.replace("_", " ").title()

def publish_tech_notes(app):
    """ Runs pelican to generate the tech notes.
        Creates a pelican config file with "live" config settings (as
        JINJA_GLOBALS) that are passed into the build.
        Throws exceptions if anything goes wrong.
        Note: this executes chdir to the tech_notes dir before executing
        the pelican command (couldn't get it to work as an internal pelican
        call).
    """
    JINJA_GLOBAL_MATCH_RE = re.compile(
      # "SOME_SETTING": "some value"
      r'\s*"([A-Z_][A-Z0-9_]+)"\s*\:\s*"([^"]*)"'
    )
    EMPTY_LINE_RE = re.compile(r'^\s*(#.*)?$')
    # root path is parent of the buggy_race_server dir containing the .py
    # TODO feels like this should be a more globally-available config
    root_path = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
    tech_notes_path = os.path.join(
        root_path, 
        app.config[ConfigSettingNames.TECH_NOTES_CONFIG_PATH.name]
    )
    full_pathname = os.path.join(
      tech_notes_path,
      app.config[ConfigSettingNames.TECH_NOTES_CONFIG_FILE_NAME.name]
    )
    conf_file_reader = open(full_pathname)
    lines = conf_file_reader.readlines()
    conf_file_reader.close()
    for i in range(len(lines)):
      stripped_line=lines[i].strip()
      if stripped_line.startswith("JINJA_GLOBALS"):
        i += 1
        while (
          (i < len(lines))
          and (
            re.match(JINJA_GLOBAL_MATCH_RE, lines[i])
            or re.match(EMPTY_LINE_RE, lines[i])
          )
        ):
          if res := re.match(JINJA_GLOBAL_MATCH_RE, lines[i]):
            (name, value) = res.groups()
            if new_value := current_app.config.get(name):
              value = new_value.replace("\"", "\\\"").replace("\n", " ")
            lines[i] = f"    \"{name}\": \"{value}\",\n"
          i += 1
    live_filename = current_app.config[ConfigSettingNames.TECH_NOTES_CONFIG_LIVE_NAME.name]
    live_config_file = open(os.path.join(tech_notes_path, live_filename), "w")
    live_config_file.writelines(lines)
    live_config_file.close()
    publish_conf_file = os.path.join(
      tech_notes_path,
      app.config.get(ConfigSettingNames.TECH_NOTES_CONFIG_PUBLISH_NAME.name)
    )
    output_path = os.path.join(
      tech_notes_path,
      app.config.get(ConfigSettingNames.TECH_NOTES_OUTPUT_PATH.name)
    )
    content_path = os.path.join(
      tech_notes_path,
      app.config.get(ConfigSettingNames.TECH_NOTES_CONTENT_PATH.name)
    )
    os.chdir(tech_notes_path)
    subprocess.run(
      [
        "pelican",
        "-s", publish_conf_file,
        "-o", output_path,
        content_path
      ],
      check=True # throw exception if this goes wrong
    )
    set_and_save_config_setting(
      app,
      name=ConfigSettingNames.TECH_NOTES_GENERATED_DATETIME.name,
      value=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
