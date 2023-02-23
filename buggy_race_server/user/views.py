# -*- coding: utf-8 -*-
"""User views."""
import time
from datetime import datetime
import threading
import markdown
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    Markup,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask_login import login_required, current_user
from functools import wraps
from wtforms import ValidationError

from buggy_race_server.admin.forms import NoteForm, NoteDeleteForm
from buggy_race_server.admin.models import Note, Task
from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.config import ConfigSettingNames
from buggy_race_server.lib.issues import IssueParser
from buggy_race_server.user.models import User
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

blueprint = Blueprint("user", __name__, url_prefix="/user", static_folder="../static")

DELAY_BEFORE_INJECTING_ISSUES = 30 # give repo generous time to get issue auth before starting

def flash_explanation_if_unauth(function):
  @wraps(function)
  def wrapper():
    if not current_user.is_authenticated:
      if request.path == '/user/settings':
        msg = "You must log in before you can access your settings"
      else:
        msg = "You must log in before you can upload data for your buggy"
      flash(msg, "warning")
    return function()
  return wrapper

@blueprint.route("/upload", strict_slashes=False)
@flash_explanation_if_unauth
@login_required
@active_user_required
@flash_suggest_if_not_yet_githubbed
def submit_buggy_data():
  """Submit the JSON for the buggy."""
  return render_template("user/submit_buggy_data.html", form = BuggyJsonForm(request.form))

@blueprint.route("/settings", strict_slashes=False)
@flash_explanation_if_unauth
@login_required
@active_user_required
def settings():
    form = ChangePasswordForm()
    return render_template(
        "user/settings.html",
        form=form,
        is_secure=True, # TODO investigate when this can be false
        server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        is_using_notes=current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name],
    )

@blueprint.route('/setup-course-repository', methods=['POST'], strict_slashes=False)
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

@blueprint.route("/password", methods=['GET','POST'], strict_slashes=False)
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
                    flash(f"Did not change {username.pretty_username}'s password: {e}", "danger")
                if is_allowed:
                     # validation confirmed username is for a real user
                    user = User.query.filter_by(username=form.username.data).first()
            if is_allowed:
                user.set_password(form.password.data)
                user.save()
                if username == current_user.username:
                  success_msg = "OK, you changed your password. Don't forget it!"
                else:
                  success_msg = f"OK, password was changed for user {username.pretty_username}"
                flash(success_msg, "success")
                return redirect(url_for("public.home"))
        else:
            flash(f"Password was not changed", "danger")
            flash_errors(form)
    usernames = []
    if current_user.is_buggy_admin:
        form.username.choices = sorted([user.username for user in User.query.all()])
        form.username.data = form.username.data or current_user.username
    return render_template("user/password.html", form=form)
  
@blueprint.route("/secret", methods=['GET','POST'], strict_slashes=False)
@flash_explanation_if_unauth
@login_required
@active_user_required
def set_api_secret():
    # note: the API secret's lifespan is hardcoded (1 hour): see pretty_lifespan below
    warn_if_insecure()
    form = ApiSecretForm()
    is_confirmation = False
    delta_mins = int((datetime.now()-current_user.api_secret_at).seconds/60) if current_user.api_secret_at else -1
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
                delta_mins = 1
        else:
            flash(f"Warning! Your API secret was not set.", "danger")
            flash_errors(form)
    return render_template(
        "user/settings_api.html",
        form=form,
        delta_mins=delta_mins,
        is_confirmation=is_confirmation,
        pretty_lifespan="one hour",
    )

@blueprint.route("/vscode-workspace", methods=['GET'], strict_slashes=False)
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
            "user/vscode_workspace.json",
            project_name=project_name,
            username=current_user.org_username or current_user.username,
            remote_server_address=remote_server_address, # e.g., linux.cim.rhul.ac.uk
            remote_server_name=remote_server_name,
            github_repo=github_repo,
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response

@blueprint.route("/note/delete", methods=['POST'])
@login_required
@active_user_required
def delete_note():
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name]:
        flash("Notes are not enabled on this project", "warning")
        abort(404)
    form = NoteDeleteForm(request.form)
    if form.validate_on_submit():
        if not form.is_confirmed.data:
            flash("Did not delete note (you didn't confirm it)", "warning")
        else:
            user = current_user # TODO: admin deletes others' notes
            note = Note.get_by_id(form.note_id.data)
            if not note:
                abort(404)
            task = Task.get_by_id(note.task_id)
            if not task or note.user_id != user.id:
                flash("Did not delete note: data mismatch", "warning")
            else:
                note.delete()
                flash(f"OK, deleted {user.pretty_username}'s note for task {task.fullname}", "success")
    else:
        flash_errors(form)
    return redirect(url_for('user.list_notes'))


@blueprint.route("/note/<task_fullname>", methods=['GET', 'POST'])
@login_required
@active_user_required
def note(task_fullname):
    """Show note for current user"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name]:
        flash("Notes are not enabled on this project", "warning")
        abort(404)
    (phase, name) = Task.split_fullname(task_fullname)
    if phase is None:
        abort(404)
    task = Task.query.filter_by(phase=phase, name=name).first()
    if task is None:
        abort(404)
    if not task.is_enabled:
        flash("Warning: this task is currently not part of the project (it's been hidden)", "danger")
    form = NoteForm(request.form)
    delete_form = NoteDeleteForm()
    user = current_user # TODO allow admins to edit notes?
    note = Note.query.filter_by(user_id=user.id, task_id=task.id).first()
    is_new_note = note is None
    if is_new_note:
        note = Note(
            user_id=current_user.id,
            task_id=task.id,
            text="",
            created_at=datetime.now())
    if request.method == "POST":
        if form.task_id.data != str(task.id):
            flash("Mismatched task in request", "danger")
            abort(400)
        if form.user_id.data != str(current_user.id):
            flash("Mismatched user in request", "danger")
            abort(400)
        if form.validate_on_submit():
            note.text = form.text.data
            if not is_new_note:
                note.modified_at = datetime.now()
            note.save()
            flash(f"OK, saved {user.pretty_username}'s note for task {task.fullname}", "success")
            return redirect(url_for("user.list_notes"))
        else:
            flash_errors(form)
    is_own_note = current_user.id == note.user_id
    return render_template(
        "user/note.html",
        user=user,
        is_own_note=is_own_note,
        is_new_note=is_new_note,
        note=note,
        task=task,
        report_type = current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
        form=form,
        delete_form=delete_form,
        pretty_timestamp=(note.modified_at or note.created_at).strftime("%Y-%m-%d %H:%M"),
    )

@blueprint.route("/notes", methods=['GET'], strict_slashes=False)
@login_required
@active_user_required
def list_notes():
    """Show all notes for current user"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name]:
        flash("Notes are not enabled on this project", "warning")
        abort(404)
    user = current_user
    tasks_by_phase = Task.get_dict_tasks_by_phase(want_hidden=False)
    notes_by_task_id = Note.get_dict_notes_by_task_id(user.id)
    return render_template(
        'user/notes.html',
        user=user,
        is_own_note=user.id == current_user.id,
        qty_notes=len(notes_by_task_id),
        tasks_by_phase=tasks_by_phase,
        notes_by_task_id=notes_by_task_id,
        report_type=current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
    )

@blueprint.route("/download/notes/<format>", methods=['GET'])
@login_required
@active_user_required
def download_notes(format):
    """Get notes for current user in HTML or text format (html or txt)"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_NOTES.name]:
        flash("Notes are not enabled on this project", "warning")
        abort(404)
    if format not in ["html", "md2html", "txt"]:
        flash("Notes can be downloaded as HTML or plain text (html or txt) only", "error")
        abort(404)
    user = current_user
    tasks_by_id = {task.id: task for task in Task.query.filter_by(is_enabled=True).all()}
    notes_by_task_id = Note.get_dict_notes_by_task_id(user.id)
    if format == "md2html":
        for task_id in notes_by_task_id:
            notes_by_task_id[task_id].text = markdown.markdown(notes_by_task_id[task_id].text)
        format = "html"
    filename = get_download_filename(f"notes-{user.username}.{format}", want_datestamp=True)        
    response = make_response(
        render_template(
            f"user/notes_download.{format}",
            username=user.username,
            notes_by_task_id=notes_by_task_id,
            tasks_by_id=tasks_by_id,
            project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
            report_type=current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
            downloaded_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            buggy_race_server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response



