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

from buggy_race_server.admin.forms import TaskTextForm, TaskTextDeleteForm
from buggy_race_server.admin.models import TaskText, Task
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
        user=current_user,
        has_fist_name=current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name],
        has_last_name=current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name],
        has_email=current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name],
        has_ext_username=current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name],
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        form=form,
        is_secure=True, # TODO investigate when this can be false
        server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        is_using_github=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name],
        is_using_texts=current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name],
        is_using_vs_workspace=current_app.config[ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name],
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
          current_app.config[ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name]
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
                  success_msg = f"OK, password was changed for user {username}"
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
    # the API secret's lifespan is hardcoded (1 hour): see pretty_lifespan below
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
    if task_names := current_app.config[ConfigSettingNames.TASK_NAME_FOR_API.name].split(","):
        api_task_names = [task_name.strip() for task_name in task_names]
    else:
        api_task_names = []
    
    return render_template(
        "user/settings_api.html",
        form=form,
        delta_mins=delta_mins,
        is_confirmation=is_confirmation,
        pretty_lifespan="one hour",
        api_task_names=api_task_names,
    )

@blueprint.route("/vscode-workspace", methods=['GET'], strict_slashes=False)
@login_required
@active_user_required
def download_vscode_workspace():
    """ Returns workspace JSON file for VScode"""
    if not current_app.config[ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name]:
        flash("VS Code workspace files are not available for this project (IS_USING_REMOTE_VS_WORKSPACE not set)", "warning")
        abort(404)
    remote_server_address = current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name]
    remote_server_name = current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name]
    if not (remote_server_address and remote_server_name):
        flash("Remote server has not been configured on the race server: cannot create VScode workspace file", "danger")
        return redirect(url_for("user.settings"))
    if not current_user.github_username:
        flash("No GitHub username (have you forked the repo yet?): cannot create VScode workspace file", "danger")
        return redirect(url_for("user.settings"))
    github_repo = current_user.course_repository
    if not github_repo:
        flash("Missing GitHub repo (have you forked the repo yet?): cannot create VScode workspace file", "danger")
        return redirect(url_for("user.settings"))
    filename = get_download_filename("buggy-editor.code-workspace")
    project_name = f"{current_app.config[ConfigSettingNames.PROJECT_CODE.name]} Buggy Editor".strip()
    response = Response(
        render_template(
            "user/vscode_workspace.json",
            project_name=project_name,
            remote_username=current_user.ext_username or current_user.username,
            remote_server_address=remote_server_address, # e.g., linux.cim.rhul.ac.uk
            remote_server_name=remote_server_name, # e.g., "the CS department's teaching server"
            github_repo=github_repo,
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response

@blueprint.route("/task-text/delete", methods=['POST'])
@login_required
@active_user_required
def delete_task_text():
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        flash("Task texts are not enabled on this project", "warning")
        abort(404)
    form = TaskTextDeleteForm(request.form)
    if form.validate_on_submit():
        if not form.is_confirmed.data:
            flash("Did not delete task text (you didn't confirm it)", "warning")
        else:
            user = current_user # TODO: admin deletes others' texts
            text = TaskText.get_by_id(form.text_id.data)
            if not text:
                abort(404)
            task = Task.get_by_id(text.task_id)
            if not task or text.user_id != user.id:
                flash("Did not delete text: data mismatch", "warning")
            else:
                text.delete()
                flash(f"OK, deleted {user.pretty_username}'s text for task {task.fullname}", "success")
    else:
        flash_errors(form)
    return redirect(url_for('user.list_task_texts'))


@blueprint.route("/task-text/<task_fullname>", methods=['GET', 'POST'])
@login_required
@active_user_required
def task_text(task_fullname):
    """Show task text for current user"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        flash(f"Task texts are not enabled on this project ({ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name} is not set)", "warning")
        abort(404)
    (phase, name) = Task.split_fullname(task_fullname)
    if phase is None:
        flash("No such task", "warning")
        abort(404)
    task = Task.query.filter_by(phase=phase, name=name).first()
    if task is None:
        if Task.query.count():
            flash("No such task", "warning")
        else:
            flash("No tasks in project yet", "warning")
        abort(404)
    if not task.is_enabled:
        flash("Warning: this task is currently not part of the project (it's been hidden)", "danger")
    form = TaskTextForm(request.form)
    delete_form = TaskTextDeleteForm()
    user = current_user # TODO allow admins to edit texts?
    tasktext = TaskText.query.filter_by(user_id=user.id, task_id=task.id).first()
    is_new_text = tasktext is None
    if is_new_text:
        tasktext = TaskText(
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
            tasktext.text = form.text.data
            if not is_new_text:
                tasktext.modified_at = datetime.now()
            tasktext.save()
            flash(f"OK, saved {user.pretty_username}'s text for task {task.fullname}", "success")
            return redirect(url_for("user.list_task_texts"))
        else:
            flash_errors(form)
    is_own_text = current_user.id == tasktext.user_id
    return render_template(
        "user/task_text.html",
        user=user,
        is_own_text=is_own_text,
        is_new_text=is_new_text,
        tasktext=tasktext,
        task=task,
        report_type = current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
        form=form,
        delete_form=delete_form,
        pretty_timestamp=(tasktext.modified_at or tasktext.created_at).strftime("%Y-%m-%d %H:%M"),
    )

@blueprint.route("/task-texts", methods=['GET'], strict_slashes=False)
@login_required
@active_user_required
def list_task_texts():
    """Show all texts for current user"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        flash("Task texts are not enabled on this project", "warning")
        abort(404)
    user = current_user
    tasks_by_phase = Task.get_dict_tasks_by_phase(want_hidden=False)
    texts_by_task_id = TaskText.get_dict_texts_by_task_id(user.id)
    return render_template(
        'user/task_texts.html',
        user=user,
        is_own_text=user.id == current_user.id,
        qty_texts=len(texts_by_task_id),
        tasks_by_phase=tasks_by_phase,
        texts_by_task_id=texts_by_task_id,
        report_type=current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
    )

@blueprint.route("/download/texts/<username>/<format>", methods=['GET'])
@login_required
@active_user_required
def download_texts(username, format):
    """Get texts for current user in HTML or text format (html or txt)"""
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        flash("Task texts are not enabled on this project", "warning")
        abort(404)
    if format not in ["html", "md2html", "txt"]:
        flash("Task texts can be downloaded as HTML or plain text (html or txt) only", "error")
        abort(404)
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f"Can't find user {username}", "danger")
        abort(404)
    if username != user.username and not current_user.is_buggy_admin:
        flash("Cannot download another user's texts", "danger")
        abort(403)
    tasks_by_id = {task.id: task for task in Task.query.filter_by(is_enabled=True).all()}
    texts_by_task_id = TaskText.get_dict_texts_by_task_id(user.id)
    if format == "md2html":
        for task_id in texts_by_task_id:
            texts_by_task_id[task_id].text = markdown.markdown(texts_by_task_id[task_id].text)
        format = "html"
    filename = get_download_filename(f"texts-{user.username}.{format}", want_datestamp=True)        
    response = make_response(
        render_template(
            f"user/task_texts_download.{format}",
            username=user.username,
            texts_by_task_id=texts_by_task_id,
            tasks_by_id=tasks_by_id,
            project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
            report_type=current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
            downloaded_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            buggy_race_server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response



