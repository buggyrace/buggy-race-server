# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request, Markup, url_for, config
from wtforms import ValidationError
from functools import wraps
from flask_login import current_user
from buggy_race_server.admin.models import Announcement

def refresh_global_announcements(app, init=False):
  if init:
    # TODO this is effectively hardcoded for now, as it's really just
    #      to help: if there are no announcements, inject a (useful)
    #      example into the database when the app fires up
    if app.config['EXAMPLE_ANNOUNCEMENT'] and Announcement.query.count()==0:
      announcement = Announcement.create(
        type="special",
        text=app.config['EXAMPLE_ANNOUNCEMENT'],
        is_html=True,
        is_visible=False,
      )
  app.config['CURRENT_ANNOUNCEMENTS'] = Announcement.query.filter_by(is_visible=True)

def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)

def warn_if_insecure():
  if not request.is_secure:
    url = request.url.replace('http://', 'https://', 1)
    flash(Markup(
      "<span class='buggy-warn'>DANGER!</span> You are not using the secure server! "
      f"<a href='{ url }' class='btn btn-warning'>Switch to &rarr; { url }</a>"),
      "danger"
    )

def flash_suggest_if_not_yet_githubbed(function):
  @wraps(function)
  def wrapper():
    if current_user and not current_user.is_github_connected():
      flash(Markup(f"You haven't connected to GitHub yet. <a href='{url_for('user.settings')}'>Do it now!</a>"), "danger")
    return function()
  return wrapper

# prevent unauthorised registration if there is an auth code in the environment
def is_authorised(field):
  auth_code = config.REGISTRATION_AUTH_CODE
  if auth_code is not None and field.data.lower() != auth_code.lower():
    raise ValidationError("You must provide a valid authorisation code")
