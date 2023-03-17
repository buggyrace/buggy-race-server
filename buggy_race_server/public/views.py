# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from datetime import datetime
from collections import defaultdict
from os import path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from buggy_race_server.admin.models import AnnouncementType
from buggy_race_server.config import ConfigSettingNames
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.extensions import login_manager
from buggy_race_server.public.forms import LoginForm
from buggy_race_server.race.models import Race
from buggy_race_server.user.forms import RegisterForm
from buggy_race_server.user.models import User
from buggy_race_server.admin.models import SocialSetting, Task

from buggy_race_server.utils import (
    active_user_required,
    flash_errors,
    get_download_filename,
    join_to_project_root,
    warn_if_insecure,
    load_config_setting,
)

blueprint = Blueprint("public", __name__, static_folder="../static")

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    warn_if_insecure()
    return render_template(
        "public/home.html",
        social_site_links=SocialSetting.get_socials_from_config(current_app.config),
        local_announcement_type=AnnouncementType.TAGLINE.value,
    )

@blueprint.route("/logout", strict_slashes=False)
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))

@blueprint.route("/login", methods=["GET", "POST"], strict_slashes=False)
def login():
    """Log in to the server."""
    warn_if_insecure()
    form = LoginForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            form.user.logged_in_at = datetime.now()
            form.user.save()
            if current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
                pretty_name = current_user.first_name or current_user.pretty_username
            else:
                pretty_name = current_user.pretty_username
            flash(f"Hello {pretty_name}! You're logged in to the race server", "success")
            if setup_status := load_config_setting(current_app, ConfigSettingNames._SETUP_STATUS.name):
                redirect_url = url_for("admin.setup")
                if current_user.is_buggy_admin:
                    session[ConfigSettingNames._SETUP_STATUS.name] = setup_status
                else:
                    flash("Not an admin user: can't do much until setup is complete", "warning")
            else:
                redirect_url = request.args.get("next") or url_for("user.submit_buggy_data")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template(
        "public/login.html",
        form=form,
        is_registration_allowed=(
            current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]
            or (not current_user.is_anonymous and current_user.is_buggy_admin)
        ),
        local_announcement_type=AnnouncementType.LOGIN.value,
        username_example=current_app.config[ConfigSettingNames.USERNAME_EXAMPLE.name],
    )

@blueprint.route("/register", methods=["GET", "POST"], strict_slashes=False)
def register():
    """Register new user.
       This is the "convenience" of allowing a single-user registration, which
       is probably most useful for adding new admins... because the "bulk
       registration" of users (i.e., students) from a CSV is probably better.
       IS_PUBLIC_REGISTRATION_ALLOWED should always be 0 (i.e., switched OFF)
       unless you're running in an enclosed environment.
    """
    form = RegisterForm(request.form)
    if current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]:
        del form.auth_code
    elif not (not current_user.is_anonymous and current_user.is_buggy_admin):
        flash(
          "You must be logged in as an administrator to register new users "
          "(you'll need to know the authorisation code too)", "warning"
        )
        abort(403)
    if not current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name]:
        del form.email
    if not current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
        del form.first_name
    if not current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name]:
        del form.last_name
    if not current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name]:
        del form.ext_username

    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            comment=form.comment.data,
            email=form.email.data if form.email else None,
            ext_username=form.ext_username.data if form.ext_username else None,
            first_name=form.first_name.data if form.first_name else None,
            is_active=True,
            is_student=form.is_student.data,
            last_name=form.last_name.data if form.last_name else None,
            latest_json="",
            password=form.password.data,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template(
        "public/register.html",
        form=form,
        is_registration_allowed=bool(current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]),
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
    )

@blueprint.route("/specs", strict_slashes=False)
def showspecs():
    """Buggy specifications page."""
    return render_template("public/specs.html",
      defaults=Buggy.DEFAULTS,
      data=Buggy.game_data
    )

@blueprint.route("/specs/data/<data_filename>")
@blueprint.route("/specs/data", strict_slashes=False)
def showspecs_data(data_filename=""):
    """Buggy specifications: data page."""
    want_mass = request.args.get('extra')=="mass" 
    if data_filename:
        if data_filename in ["types.json", "defaults.json"]:
            if data_filename == "defaults.json":
                download = make_response(jsonify(Buggy.DEFAULTS))
            else:
                download = make_response(jsonify(Buggy.game_data))
            download.headers["Content-Disposition"] = f"attachment; filename={get_download_filename(data_filename)}"
            download.headers["Content-type"] = "application/json"
            return download
        else:
            abort(404)
    return render_template(
        "public/specs_data.html", 
        defaults=Buggy.DEFAULTS,
        data=Buggy.game_data,
        is_showing_mass=want_mass
    )

@blueprint.route("/about", strict_slashes=False)
def about():
    """About page."""
    form = LoginForm(request.form)
    response = make_response(render_template("public/about.html", form=form))
    response.headers.set("Cache-Control", "no-cache")
    return response

@blueprint.route("/race", strict_slashes=False)
def announce_races():
    """Race announcement page."""
    next_race=Race.query.filter(
        Race.is_visible==True,
        Race.start_at > datetime.now()
      ).order_by(Race.start_at.asc()).first()
    races = Race.query.filter(
            Race.is_visible==True,
            Race.start_at < datetime.now()
          ).all()
    return render_template("public/race.html",
      next_race=next_race,
      races=races)

def _send_tech_notes_assets(type, path):
    try:
        if type not in ["theme", "assets"]:
            raise FileNotFoundError()
        return send_file(
            join_to_project_root(
                current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                current_app.config[ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name],
                type,
                path
            )
        )
    except FileNotFoundError:
        return "File not found", 404

@blueprint.route("/project/tasks/<task_id>", strict_slashes=False)
def show_single_task(task_id):
    """Redirect individual tasks to single task page, with anchor tag"""
    task_id = task_id.lower()
    if not task_id.startswith(Task.ANCHOR_PREFIX):
        task_id = f"{Task.ANCHOR_PREFIX}{task_id}"
    url = url_for("public.serve_project_page", page="tasks")
    return redirect(f"{url}#{task_id}", code=301 )

@blueprint.route("/project", strict_slashes=False)
@blueprint.route("/project/<page>", strict_slashes=False)
def serve_project_page(page=None):
    tasks = []
    if page == "tasks":
        task_html_filename = current_app.config[ConfigSettingNames._TASK_LIST_HTML_FILENAME.name]
        generated_task_file = join_to_project_root(
            current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
            task_html_filename
        )
        if not path.exists(generated_task_file):
            flash(f"Task list ({task_html_filename}) is missing: an administrator needs to update it", "danger")
            abort(404)
        try:
            html_file = open(generated_task_file, "r")
            task_html = "".join(html_file.readlines())
            html_file.close()
        except IOError as e:
            flash(f"Error reading task list from {task_html_filename}: {e}", "danger")
            abort(500)
        return render_template(
            "public/project/tasks.html",
            task_html=task_html
        )
    elif page is None or page == "index":
        template = "public/project/index.html"
    elif page in ["poster", "report"]:
        if not current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name]:
            abort(404) # nothing to show if there's no report
        tasks = Task.query.filter_by(is_enabled=True).order_by(
                    Task.phase.asc(),
                    Task.sort_position.asc()
                ).all()
        template = "public/project/report.html"
    elif page == "workflow":
        if not current_app.config[ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name]:
            abort(404)
        if url := current_app.config[ConfigSettingNames.PROJECT_WORKFLOW_URL.name]:
            return redirect(url)
        template = "public/project/workflow.html"
    else:
        abort(404)
    report_type = current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name]
    is_report = bool(report_type) # if it's not empty string (or maybe None?)
    return render_template(
        template,
        expected_phase_completion=current_app.config[ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name],
        is_report=is_report,
        is_showing_project_workflow=current_app.config[ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name],
        is_storing_texts=current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name],
        is_zip_info_displayed=current_app.config[ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name],
        project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
        report_type=report_type,
        site_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        submission_link=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_LINK.name],
        submit_deadline=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name],
        tasks=tasks,
        workflow_url=current_app.config[ConfigSettingNames.PROJECT_WORKFLOW_URL.name],
    )

@blueprint.route("/assets/<path:path>")
def send_project_assets(path):
    return _send_tech_notes_assets("assets", path)

@blueprint.route("/theme/<path:path>")
def send_project_theme(path):
    return _send_tech_notes_assets("theme", path)

@blueprint.route("/tech-notes", strict_slashes=False)
def tech_notes_redirect_to_index():
    external_url = current_app.config.get("TECH_NOTES_EXTERNAL_URL")
    if external_url:
        return redirect(f"{external_url}/index")
    else:
        return redirect(url_for("public.serve_tech_notes", path="index"))

@blueprint.route("/tech-notes/<path:path>", strict_slashes=False)
def serve_tech_notes(path=None):
    external_url = current_app.config.get(ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name)
    if not path:
        path = "index.html"
    elif path.endswith("/"):
        path +=" index.html"
    elif not path.endswith(".html"):
        path += ".html"
    # TODO sanitise the path
    if external_url:
        return redirect(f"{external_url}/{path}")
    try:
        return send_file(
            join_to_project_root(
                current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                current_app.config[ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name],
                current_app.config[ConfigSettingNames._TECH_NOTES_PAGES_DIR.name],
                path
            )
        )
    except FileNotFoundError as e:
        abort(404)

