# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, request, Markup, url_for
from functools import wraps
from flask_login import current_user


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
