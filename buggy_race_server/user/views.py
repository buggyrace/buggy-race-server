# -*- coding: utf-8 -*-
"""User views."""
import time
from datetime import datetime, timezone
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
from buggy_race_server.config import AnnouncementTypes, ConfigSettingNames
from buggy_race_server.lib.issues import IssueParser
from buggy_race_server.user.models import User
from buggy_race_server.user.forms import ChangePasswordForm, ApiSecretForm
from buggy_race_server.utils import (
    active_user_required,
    join_to_project_root,
    flash_errors,
    get_download_filename,
    get_pretty_approx_duration,
    is_authorised,
    warn_if_insecure,
)

blueprint = Blueprint("user", __name__, url_prefix="/user", static_folder="../static")

DELAY_BEFORE_INJECTING_ISSUES = 30 # give repo generous time to get issue auth before starting

def flash_explanation_if_unauth(msg):
    """Improve a 403 by explaining what it is you could do if you were logged in"""
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not (current_user.is_authenticated and current_user.is_active):
                if msg: flash(msg, "warning")
            return function(*args, **kwargs)
        return decorated_function
    return decorator

@blueprint.route("/new")
def register_new_user():
    if not current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]:
        flash(
          "You must be logged in as an administrator to register new users "
          "(public registration is not enabled)", "warning"
        )
        abort(403)
    return redirect(url_for('admin.new_user'))

@blueprint.route("/upload", strict_slashes=False)
@flash_explanation_if_unauth("You must log in before you can upload data for your buggy ")
@login_required
@active_user_required
def submit_buggy_data():
    """Submit the JSON for the buggy."""
    if (
        current_app.config[ConfigSettingNames.IS_USING_GITHUB.name]
        and
        current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name]
        and
        not current_user.is_github_connected()
    ):
        flash(
            Markup(
                "You haven't connected to GitHub yet. "
                f"<a href='{url_for('user.settings')}'>Do it now!</a>"
            ),
            "danger"
        )
    return render_template(
        "user/submit_buggy_data.html",
        form=BuggyJsonForm(request.form)
    )

@blueprint.route("/settings", strict_slashes=False)
@flash_explanation_if_unauth("You must log in before you can access your settings")
@login_required
@active_user_required
def settings():
    form = ChangePasswordForm()
    is_using_github = (
        current_app.config[ConfigSettingNames.IS_USING_GITHUB.name]
        and current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name]
    )
    return render_template(
        "user/settings.html",
        ext_id_name=current_app.config[ConfigSettingNames.EXT_ID_NAME.name],
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        form=form,
        has_email=current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name],
        has_ext_id=current_app.config[ConfigSettingNames.USERS_HAVE_EXT_ID.name],
        has_ext_username=current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name],
        has_fist_name=current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name],
        has_last_name=current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name],
        is_secure=True, # TODO investigate when this can be false
        is_using_github=is_using_github,
        is_using_texts=current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name],
        is_using_vs_workspace=current_app.config[ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name],
        local_announcement_type=AnnouncementTypes.GET_EDITOR.value,
        project_remote_server_address=current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_ADDRESS.name],
        project_remote_server_name=current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_NAME.name],
        server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        user=current_user,
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
          current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
          current_app.config[ConfigSettingNames._BUGGY_EDITOR_ISSUES_CSV_FILE.name]
        )
    )

    def inject_issues_into_repo(user, repo_name, issues_parser):
        # passing arguments to avoid dependency on app context (this runs in another thread)
        #
        # CONTEXT ONY: ---Issues appear in most recent order and we want the first task
        # to appear as the most recent issue!---
        #
        # Except then when the github api rate limits us, the first issues
        # don't get delivered :(
        for i, issue in enumerate(issues_parser.parse_issues()):
            response = user.github.post(
                f"/repos/{user.github_username}/{repo_name}/issues",
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
    #
    # Note: inject_issues_into_repo must will run _without_ an app context
    threading.Timer(
        DELAY_BEFORE_INJECTING_ISSUES,
        inject_issues_into_repo,
        args=[
          current_user._get_current_object(),
          current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name],
          issues_parser,
        ]
    ).start()

    return redirect(url_for('user.settings'))

@blueprint.route("/password/<username>", methods=['GET'], strict_slashes=False)
@blueprint.route("/password", methods=['GET','POST'], strict_slashes=False)
@login_required
@active_user_required
def change_password(username=None):
    """Change user's password (staff may be able to change another user's password)."""
    warn_if_insecure()
    form = ChangePasswordForm(request.form)
    is_ta_password_change_enabled = current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name]
    users_pw_can_be_changed = []
    admin_usernames = []
    if (current_user.is_administrator 
        or
        (current_user.is_teaching_assistant and is_ta_password_change_enabled)
    ):
        users = User.query.filter(User.is_active==True).all()
        if not current_user.is_administrator:
            users = [user for user in users if not user.is_staff]
        users_pw_can_be_changed = [user.username for user in users]
        admin_usernames = [user.username for user in users if user.is_administrator]
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            username = form.username.data
            username = username.lower().strip() if username else current_user.username
            is_allowed = False
            if current_user.username == username:
                is_allowed = True
                target_user = current_user
            elif current_user.is_staff:
                target_user = User.query.filter_by(username=username).first()
                if target_user is None: # actually was confirmed by validation
                    abort(404)
                if current_user.is_administrator:
                    if target_user.is_administrator:
                        try:
                            is_allowed = is_authorised(form, form.auth_code)
                        except ValidationError as e:
                            flash(
                                "You must provide a valid authorisation code "
                                "to change another admin's password",
                                "warning"
                            )
                            flash("Did not change pasword", "danger")
                    else:
                        is_allowed = True
                elif target_user.is_staff:
                    is_allowed = False
                    flash(
                        "Only administratrors can change another staff member's password",
                        "warning"
                    )
                elif is_ta_password_change_enabled:
                    # teaching assistant changing a non-staff password
                    is_allowed = True
                elif not is_allowed:
                    flash("You cannot change another user's password", "danger")
            else: # non-staff member trying to change someone else's pw
                flash("You cannot change another user's password", "danger")
            if is_allowed:
                target_user.set_password(form.password.data)
                target_user.save()
                if username == current_user.username:
                   success_msg = "OK, you changed your password. Don't forget it!"
                else:
                    success_msg = f"OK, password was changed for user {target_user.pretty_username}"
                flash(success_msg, "success")
                return redirect(url_for("public.home"))
        else:
            flash(f"Password was not changed", "danger")
            flash_errors(form)
    if current_user.username not in users_pw_can_be_changed:
        users_pw_can_be_changed.append(current_user.username)
    form.username.choices = sorted(users_pw_can_be_changed)
    form.username.data = form.username.data or username or current_user.username
    return render_template(
        "user/password.html",
        admin_usernames_str=",".join(admin_usernames),
        form=form,
        is_more_than_one_username=len(users_pw_can_be_changed) > 1,
        username=username,
    )
  
@blueprint.route("/api", methods=['GET','POST'], strict_slashes=False)
@flash_explanation_if_unauth("You must log in before you can access your settings")
@login_required
@active_user_required
def set_api_secret():
    # the API secret's lifespan is hardcoded (1 hour): see pretty_lifespan below
    warn_if_insecure()
    form = ApiSecretForm()
    is_confirmation = False
    if current_user.api_secret_at:
        now_utc = datetime.now(timezone.utc)
        try:
            delta_mins =  now_utc - current_user.api_secret_at
        except TypeError as error:
            # TODO the current_user.api_secret_at WAS NAIVE (but how? just saved it as UTC)
            # TODO see issue #139
            delta_mins = now_utc - current_user.api_secret_at.replace(tzinfo=timezone.utc)
        delta_mins = int(delta_mins.seconds/60)
    else:
        delta_mins = -1
    is_api_secret_otp=current_app.config[ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name]
    is_student_api_otp_allowed=current_app.config[ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name]
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if current_user.api_secret == form.api_secret.data:
                flash(f"Warning! Your API secret was not set: must be different from the last one.", "danger")
            else:
                current_user.api_secret = form.api_secret.data
                current_user.api_secret_at = datetime.now(timezone.utc)
                current_user.api_secret_count = 0
                if is_student_api_otp_allowed:
                    current_user.is_api_secret_otp = form.is_one_time_password.data
                else:
                    current_user.is_api_secret_otp = is_api_secret_otp
                current_user.save()
                pretty_ttl = get_pretty_approx_duration(current_app.config[ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name])
                flash(f"OK, you set your API secret: it's good for about {pretty_ttl} from now.", "success")
                is_confirmation = True
                delta_mins = 1
        else:
            flash(f"Warning! Your API secret was not set.", "danger")
            flash_errors(form)
    api_task_name = current_app.config[ConfigSettingNames.TASK_NAME_FOR_API.name]
    return render_template(
        "user/settings_api.html",
        form=form,
        delta_mins=delta_mins,
        is_confirmation=is_confirmation,
        pretty_lifespan=get_pretty_approx_duration(
            current_app.config[ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name]
        ),
        is_api_secret_otp=is_api_secret_otp,
        is_student_api_otp_allowed=is_student_api_otp_allowed,
        api_task_name=api_task_name,
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
    if form.is_submitted() and form.validate():
        if not form.is_confirmed.data:
            flash("Did not delete task text (you didn't confirm it)", "danger")
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
            created_at=datetime.now(timezone.utc))
    if request.method == "POST":
        if form.task_id.data != str(task.id):
            flash("Mismatched task in request", "danger")
            abort(400)
        if form.user_id.data != str(current_user.id):
            flash("Mismatched user in request", "danger")
            abort(400)
        if form.is_submitted() and form.validate():
            tasktext.text = form.text.data
            if not is_new_text:
                tasktext.modified_at = datetime.now(timezone.utc)
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
@flash_explanation_if_unauth("You must log in before you can access or edit your texts")
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
    if username != user.username and not current_user.is_staff:
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
            downloaded_at=datetime.now(current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name]).strftime("%Y-%m-%d %H:%M"),
            buggy_race_server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        )
    )
    response.headers['content-disposition'] = f"attachment; filename=\"{filename}\""
    return response



