# -*- coding: utf-8 -*-
"""User views."""
import os
import csv
import time
import threading
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for, current_app, Markup, Response
from flask_login import login_required, current_user
from functools import wraps
from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.user.models import User
from buggy_race_server.lib.issues import IssueParser
from buggy_race_server.user.forms import ChangePasswordForm, ApiSecretForm
from buggy_race_server.utils import flash_errors, warn_if_insecure, flash_suggest_if_not_yet_githubbed
from datetime import datetime

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")

DELAY_BEFORE_INJECTING_ISSUES = 30 # give repo generous time to get issue auth before starting

def flash_explanation_if_unauth(function):
  @wraps(function)
  def wrapper():
    if not current_user.is_authenticated:
      if request.path == '/users/settings':
        msg = "You must log in before you can access your settings"
      else:
        msg = "You must log in before you can upload data for your buggy"
      flash(msg, "warning")
    return function()
  return wrapper

@blueprint.route("/")
@flash_explanation_if_unauth
@login_required
@flash_suggest_if_not_yet_githubbed
def submit_buggy_data():
  """Submit the JSON for the buggy."""
  return render_template("users/submit_buggy_data.html", form = BuggyJsonForm(request.form))

@blueprint.route("/settings")
@flash_explanation_if_unauth
@login_required
def settings():
    form = ChangePasswordForm()
    return render_template(
        "users/settings.html",
        form=form,
        server_url=current_app.config['BUGGY_RACE_SERVER_URL']
    )

@blueprint.route('/setup-course-repository', methods=['POST'])
@login_required
def setup_course_repository():
    """Create a new fork of the BUGGY_EDITOR_REPO if one doesn't already exist"""
    if current_user.has_course_repository():
        flash("Didn't try to fork: it looks like there's already a repo there", "danger")
        return redirect(url_for('user.settings'))

    # Forking is async so we assume we're successful and hope for the best!
    repo = current_user.github.post(f"/repos/{current_app.config['BUGGY_EDITOR_REPO_OWNER']}/{current_app.config['BUGGY_EDITOR_REPO_NAME']}/forks")

    # Forks don't get issues by default
    current_user.github.patch(
        f"/repos/{current_user.github_username}/{current_app.config['BUGGY_EDITOR_REPO_NAME']}",
        {}, { 'has_issues': 'true'}
    )


    # this could probably be cached?
    # needs to run in current app context (same thread)
    issues_parser = IssueParser(
        os.path.join(
          current_app.root_path, current_app.config['BUGGY_EDITOR_ISSUES_FILE']
        )
    )

    def create_issues(user):
        # CONTEXT ONY: ---Issues appear in most recent order and we want the first task
        # to appear as the most recent issue!---
        #
        # Except then when the github api rate limits us, the first issues
        # don't get delivered :(
        for i, issue in enumerate(issues_parser.parse_issues()):
            response = user.github.post(
                f"/repos/{user.github_username}/{current_app.config['BUGGY_EDITOR_REPO_NAME']}/issues",
                {},
                {
                    'title': issue['title'],
                    'body': issue['body'],
                    'assignees': [user.github_username]
                }
            )

            # We were trigger abuse stuff from github so go slowly!
            # See here: https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-abuse-rate-limits
            time.sleep(2.0)

    # delay here in case the has_issues patch is taking a while to authenticate...
    # since the repo is always being made but the first 1d6 issues aren't making it
    threading.Timer(
        DELAY_BEFORE_INJECTING_ISSUES,
        create_issues,
        args=[current_user._get_current_object()]
    ).start()

    return redirect(url_for('user.settings'))

@blueprint.route("/password", methods=['GET','POST'])
@login_required
def change_password():
    """Change user's password (must be current user unless admin)."""
    warn_if_insecure()
    form = ChangePasswordForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            is_allowed = True
            username = form.username.data
            user = current_user
            if current_user.username != username:
                if username == "":
                    username = current_user.username
                elif not current_user.is_buggy_admin:
                    flash("Cannot change another user's password", "danger")
                    is_allowed = False
                else: # user was checked by validation
                    user = User.query.filter_by(username=form.username.data).first()
            if is_allowed:
                user.set_password(form.password.data)
                user.save()
                if username == current_user.username:
                  success_msg = "OK, you changed your password. Don't forget it!"
                else:
                  success_msg = f"OK, password was changed for user {username}"
                flash(success_msg, "success")
                return redirect(url_for("public.home"))
        else:
            flash(f"Password was not changed", "danger")
            flash_errors(form)
    return render_template("users/password.html", form=form)
  
@blueprint.route("/secret", methods=['GET','POST'])
@flash_explanation_if_unauth
@login_required
def set_api_secret():
    # note: the API secret's lifespan is hardcoded (1 hour): see pretty_lifespan below
    warn_if_insecure()
    is_confirmation = False
    form = ApiSecretForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if current_user.api_secret == form.api_secret.data:
                flash(f"Warning! Your API secret was not set: must be different from the last one.", "danger")
            else:
                current_user.api_secret = form.api_secret.data
                current_user.api_secret_at = datetime.now()
                current_user.save()
                flash("OK, you set your API secret: it's good for one hour from now.", "success")
                is_confirmation = True
        else:
            flash(f"Warning! Your API secret was not set.", "danger")
            flash_errors(form)
    delta_mins = int((datetime.now()-current_user.api_secret_at).seconds/60) if current_user.api_secret_at else -1
    return render_template("users/api_secret.html", form=form, delta_mins=delta_mins,
        is_confirmation=is_confirmation, pretty_lifespan="one hour")

@blueprint.route("/vscode-workspace", methods=['GET'])
@login_required
def vscode_workspace():
  response = Response(render_template("users/vscode_workspace.json"))
  response.headers['content-disposition'] = f"attachment; filename=\"{current_app.config['PROJECT_SLUG']}.code-workspace\""
  print(response.headers.__dict__)
  return response
