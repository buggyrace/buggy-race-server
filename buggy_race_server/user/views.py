# -*- coding: utf-8 -*-
"""User views."""
import os
import csv
import time
from datetime import datetime
import threading
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for, current_app, Markup, Response
from flask_login import login_required, current_user
from functools import wraps
from wtforms import ValidationError

from buggy_race_server.config import ConfigSettingNames
from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.user.models import User
from buggy_race_server.lib.issues import IssueParser
from buggy_race_server.user.forms import ChangePasswordForm, ApiSecretForm
from buggy_race_server.utils import (
    active_user_required,
    join_to_project_root,
    flash_errors,
    flash_suggest_if_not_yet_githubbed,
    get_download_filename,
    is_authorised,
    warn_if_insecure,
)

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
@active_user_required
@flash_suggest_if_not_yet_githubbed
def submit_buggy_data():
  """Submit the JSON for the buggy."""
  return render_template("users/submit_buggy_data.html", form = BuggyJsonForm(request.form))

@blueprint.route("/settings")
@flash_explanation_if_unauth
@login_required
@active_user_required
def settings():
    form = ChangePasswordForm()
    return render_template(
        "users/settings.html",
        form=form,
        is_secure=True, # TODO investigate when this can be false
        server_url=current_app.config['BUGGY_RACE_SERVER_URL']
    )

@blueprint.route('/setup-course-repository', methods=['POST'])
@login_required
@active_user_required
def setup_course_repository():
    """Create a new fork of the BUGGY_EDITOR_REPO if one doesn't already exist"""
    if current_user.has_course_repository():
        flash("Didn't try to fork: it looks like there's already a repo there", "danger")
        return redirect(url_for('user.settings'))

    # Forking is async so we assume we're successful and hope for the best!
    repo = current_user.github.post(
        f"/repos/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name]}"
        f"/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name]}/forks")

    # Forks don't get issues by default
    current_user.github.patch(
        f"/repos/{current_user.github_username}/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name]}",
        {},
        { 'has_issues': 'true'}
    )

    # this could probably be cached?
    # needs to run in current app context (same thread)
    issues_parser = IssueParser(
        join_to_project_root(
          "project",
          current_app.config[ConfigSettingNames.BUGGY_EDITOR_ISSUES_FILE.name]
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
                f"/repos/{user.github_username}/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name]}/issues",
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
@active_user_required
def change_password():
    """Change user's password (must be current user unless admin)."""
    warn_if_insecure()
    form = ChangePasswordForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data
            username = username.lower().strip() if username else current_user.username
            if is_allowed := current_user.username == username:
                user = current_user
            elif not current_user.is_buggy_admin:
                flash("You cannot change another user's password", "danger")
            else: # is_allowed is False
                try:
                    is_allowed = is_authorised(form, form.auth_code)
                except ValidationError as e:
                    flash(f"Did not change {username}'s password: {e}", "danger")
                if is_allowed:
                     # validation confirmed username is for a real user
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
    usernames = []
    if current_user.is_buggy_admin:
        form.username.choices =  [""]+sorted([user.username for user in User.query.all()])
    return render_template("users/password.html", form=form)
  
@blueprint.route("/secret", methods=['GET','POST'])
@flash_explanation_if_unauth
@login_required
@active_user_required
def set_api_secret():
    # note: the API secret's lifespan is hardcoded (1 hour): see pretty_lifespan below
    warn_if_insecure()
    form = ApiSecretForm()
    is_confirmation = False
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
@active_user_required
def vscode_workspace():
    """ Returns workspace JSON file for VScode"""
    remote_server_address = current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name]
    remote_server_name = current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name]
    if not (remote_server_address and remote_server_name):
        return "Remote server has not been configured on the race server: cannot supply VS workspace file", 400
    if not current_user.github_username:
        return "No GitHub username (have you forked the repo yet?): cannot supply VS workspace file", 400
    github_repo = current_user.course_repository
    if not github_repo:
        return "Missing GitHub repo (have you forked the repo yet?): cannot supply VS workspace file", 400
    filename = get_download_filename("buggy-editor.code-workspace")
    project_name = f"{current_app.config[ConfigSettingNames.PROJECT_CODE.name]} Buggy Editor".strip()
    response = Response(
        render_template(
            "users/vscode_workspace.json",
            project_name=project_name,
            username=current_user.org_username or current_user.username,
            remote_server_address=remote_server_address, # e.g., linux.cim.rhul.ac.uk
            remote_server_name=remote_server_name,
            github_repo=github_repo,
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response
