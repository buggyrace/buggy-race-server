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
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

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
        social_site_links=SocialSetting.get_socials_from_config(current_app.config)
    )

@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))

@blueprint.route("/login/", methods=["GET", "POST"])
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
        )
    )

@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
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
    if not current_app.config[ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name]:
        del form.org_username

    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            org_username=form.org_username.data if form.org_username else None,
            email=form.email.data if form.email else None,
            first_name=form.first_name.data if form.first_name else None,
            last_name=form.last_name.data if form.last_name else None,
            password=form.password.data,
            is_student=form.is_student.data,
            notes=form.notes.data,
            is_active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template(
        "public/register.html",
        form=form,
        is_registration_allowed=bool(current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name])
    )

@blueprint.route("/specs/")
def showspecs():
    """Buggy specifications page."""
    return render_template("public/specs.html",
      defaults=Buggy.DEFAULTS,
      data=Buggy.game_data
    )

@blueprint.route("/specs/data/<data_filename>")
@blueprint.route("/specs/data")
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

@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)

@blueprint.route("/race/")
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

@blueprint.route("/buggy/")
@blueprint.route("/buggy/<username>")
@login_required
@active_user_required
def show_buggy(username=None):
    """Admin inspection of buggy for given user."""
    if username is None:
        user = current_user
        username = user.username
    else:
        if not current_user.is_buggy_admin:
          abort(403)
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f"Cannot show buggy: no such user \"{username}\"", "danger")
            return redirect(url_for("public.home"))
    users_buggy = Buggy.query.filter_by(user_id=user.id).first()
    is_plain_flag = True
    if users_buggy is None:
        flash("No buggy exists for this user", "danger")
    else:
        is_plain_flag = users_buggy.flag_pattern == 'plain'
    return render_template("users/show_buggy.html",
        is_own_buggy=user==current_user,
        user=user,
        buggy=users_buggy,
        is_plain_flag=is_plain_flag
    )

def _send_tech_notes_assets(type, path):
    try:
        if type not in ["theme", "assets"]:
            raise FileNotFoundError()
        return send_file(
            join_to_project_root(
                current_app.config[ConfigSettingNames.TECH_NOTES_PATH.name],
                current_app.config[ConfigSettingNames.TECH_NOTES_OUTPUT_DIR.name],
                type,
                path
            )
        )
    except FileNotFoundError:
        return "File not found", 404

@blueprint.route("/project/tasks/<task_id>")
def show_single_task(task_id):
    """Redirect individual tasks to single task page, with anchor tag"""
    task_id = task_id.lower()
    if not task_id.startswith("task-"):
        task_id = f"task-{task_id}"
    url = current_app.config.get("GITHUB_PAGES_URL") or ""
    return redirect(f"{url}/project/tasks/#{task_id}", code=301 )

@blueprint.route("/project", strict_slashes=False)
@blueprint.route("/project/<page>", strict_slashes=False)
def serve_project_page(page=None):
    tasks = []
    if page == "tasks":
        filename = current_app.config[ConfigSettingNames.TASK_LIST_TEMPLATE.name]
        generated_task_file = join_to_project_root(
            current_app.config[ConfigSettingNames.TECH_NOTES_PATH.name],
            current_app.config[ConfigSettingNames.TECH_NOTES_OUTPUT_DIR.name],
            filename
        )
        if not path.exists(generated_task_file):
            flash(f"Task list ({filename}) is missing: an administrator needs to update it", "danger")
            abort(404)
        return send_file(generated_task_file)
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
        template = "public/project/workflow.html"
    else:
        abort(404)
    report_type = current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name]
    is_report = bool(report_type) # if it's not empty string (or maybe None?)
    submit_deadline = current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name]
    workflow_url = current_app.config[ConfigSettingNames.PROJECT_WORKFLOW_URL.name]
    if workflow_url and not workflow_url.startswith("http"):
        workflow_url = "/project/workflow" # if it's not a URL, force it
    return render_template(
        template,
        site_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
        is_report=is_report,
        report_type=report_type,
        expected_phase_completion=current_app.config[ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name],
        submit_deadline=submit_deadline,
        submission_link=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_LINK.name],
        is_zip_info_displayed=current_app.config[ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name],
        workflow_url=workflow_url,
        tasks=tasks,
    )

@blueprint.route("/assets/<path:path>")
def send_project_assets(path):
    return _send_tech_notes_assets("assets", path)

@blueprint.route("/theme/<path:path>")
def send_project_theme(path):
    return _send_tech_notes_assets("theme", path)

@blueprint.route("/tech-notes", strict_slashes=False)
def tech_notes_redirect_to_index():
    url = current_app.config.get("GITHUB_PAGES_URL") or ""
    return redirect(f"{url}/tech-notes/index", code=301 )

@blueprint.route("/tech-notes/<path:path>")
def serve_tech_notes(path=None):
    if not path:
        path = "index.html"
    elif path.endswith("/"):
        path +=" index.html"
    elif not path.endswith(".html"):
        path += ".html"
    # TODO sanitise the path
    try:
        return send_file(
            join_to_project_root(
                current_app.config[ConfigSettingNames.TECH_NOTES_PAGES_PATH.name],
                path
            )
        )
    except FileNotFoundError as e:
        abort(404)

