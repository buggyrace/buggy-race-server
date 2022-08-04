# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request, Markup, url_for, config
from wtforms import ValidationError
from functools import wraps
from flask_login import current_user
from buggy_race_server.config import ConfigFromEnv
from buggy_race_server.admin.models import Announcement

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
  auth_code = ConfigFromEnv.REGISTRATION_AUTH_CODE
  if auth_code is not None and field.data.lower() != auth_code.lower():
    raise ValidationError("You must provide a valid authorisation code")
