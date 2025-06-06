# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from datetime import datetime, timezone
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
from markupsafe import Markup

from buggy_race_server.database import db
from buggy_race_server.config import AnnouncementTypes, ConfigSettingNames, DistribMethods
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.extensions import login_manager
from buggy_race_server.public.forms import LoginForm
from buggy_race_server.race.models import Race, RaceResult
from buggy_race_server.user.models import User
from buggy_race_server.admin.models import DbFile, LinkedSiteSettings, Task

from buggy_race_server.utils import (
    flash_errors,
    get_day_of_week,
    get_download_filename,
    get_buggy_editor_local_url,
    join_to_project_root,
    warn_if_insecure,
    load_config_setting,
    get_flag_color_css_defs,
    is_poster,
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
    editor_url = ""
    if current_app.config[ConfigSettingNames.EDITOR_DISTRIBUTION_METHOD.name]==DistribMethods.ZIP.value:
        editor_url = editor_url = url_for("public.download_editor_zip")
    elif current_app.config[ConfigSettingNames.EDITOR_DISTRIBUTION_METHOD.name]==DistribMethods.PRELOAD.value:
        if current_user and current_user.is_authenticated:
            editor_url = current_user.editor_repo_url
    elif current_app.config[ConfigSettingNames.IS_USING_VCS.name]:
        editor_url = current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_URL.name]
    else:
        # note: this itself redirects if there's an explicit download URL set
        editor_url = url_for("public.download_editor_zip")
    is_using_vcs = (
        current_app.config[ConfigSettingNames.IS_USING_VCS.name]
        or
        current_app.config[ConfigSettingNames.IS_STUDENT_USING_REPO.name]
    )
    vcs_name = current_app.config[ConfigSettingNames.VCS_NAME.name]
    source_code_icon = "icon-embed2"
    if is_using_vcs and vcs_name:
        if vcs_name.lower() == "github":
          source_code_icon = "icon-github"
        # elif vcs_name.lower() == "gitlab":  # TODO: also gitlab and svn?
        #   source_code_icon = "icon-gitlab"
    return render_template(
        "public/home.html",
        editor_url=editor_url,
        is_downloading_zip=current_app.config[ConfigSettingNames.EDITOR_DISTRIBUTION_METHOD.name]==DistribMethods.ZIP.value,
        is_preloaded_repos=current_app.config[ConfigSettingNames.EDITOR_DISTRIBUTION_METHOD.name]==DistribMethods.PRELOAD.value,
        is_showing_tech_notes=current_app.config[ConfigSettingNames.IS_SHOWING_TECH_NOTES.name],
        is_forking_github=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name],
        is_using_vcs=is_using_vcs,
        local_announcement_type=AnnouncementTypes.TAGLINE.value,
        external_site_links=LinkedSiteSettings.get_linked_sites_from_config(current_app.config),
        source_code_icon=source_code_icon,
        vcs_name=vcs_name,
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
        if form.is_submitted() and form.validate():
            login_user(form.user)
            is_showing_change_password_msg = current_app.config[
                ConfigSettingNames.IS_USER_TOLD_TO_CHANGE_PASSWORD.name
            ]
            form.user.logged_in_at = datetime.now(timezone.utc)
            if form.user.first_logged_in_at is None:
                form.user.first_logged_in_at = form.user.logged_in_at
                if not current_user.is_student:
                    is_showing_change_password_msg = False
            else:
                is_showing_change_password_msg = False
            form.user.save()
            if current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
                pretty_name = current_user.first_name or current_user.pretty_username
            else:
                pretty_name = current_user.pretty_username
            flash(f"Hello {pretty_name}! You're logged in to the race server", "success")
            if not current_user.is_login_enabled and current_user.is_administrator:
                flash(f"Your login is disabled, but that was ignored because you're an administrator", "info")
            if setup_status := load_config_setting(current_app, ConfigSettingNames._SETUP_STATUS.name):
                redirect_url = url_for("admin.setup")
                if current_user.is_administrator:
                    session[ConfigSettingNames._SETUP_STATUS.name] = setup_status
                else:
                    flash("Not an admin user: can't do much until setup is complete", "warning")
            else:
                redirect_url = request.args.get("next") or (
                    url_for("admin.admin") if current_user.is_staff
                    else url_for("user.home_page")
                )
            if is_showing_change_password_msg:
                flash(
                    Markup(
                        "Remember to <a href=\""
                        f"${url_for('user.change_password')}\">change your password</a>!"
                    ),
                    "warning"
                )
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template(
        "public/login.html",
        form=form,
        is_registration_allowed=(
            current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]
            or (not current_user.is_anonymous and current_user.is_administrator)
        ),
        
        local_announcement_type=AnnouncementTypes.LOGIN.value,
        username_example=current_app.config[ConfigSettingNames.USERNAME_EXAMPLE.name],
    )

@blueprint.route("/register")
def register_new_user():
    return redirect(url_for('admin.new_user'))

@blueprint.route("/specs", strict_slashes=False)
def show_specs():
    """Buggy specifications page."""
    return render_template("public/specs.html",
      defaults=Buggy.DEFAULTS,
      data=Buggy.GAME_DATA
    )

@blueprint.route("/specs/data/<data_filename>")
@blueprint.route("/specs/data", strict_slashes=False)
def show_specs_data(data_filename=""):
    """Buggy specifications: data page."""
    want_mass = request.args.get('extra')=="mass" 
    if data_filename:
        if data_filename in ["types.json", "defaults.json"]:
            if data_filename == "defaults.json":
                download = make_response(jsonify(Buggy.DEFAULTS))
            else:
                download = make_response(jsonify(Buggy.GAME_DATA))
            download.headers["Content-Disposition"] = f"attachment; filename={get_download_filename(data_filename)}"
            download.headers["Content-type"] = "application/json"
            return download
        else:
            abort(404)
    return render_template(
        "public/specs_data.html", 
        defaults=Buggy.DEFAULTS,
        data=Buggy.GAME_DATA,
        is_showing_mass=want_mass
    )

@blueprint.route("/about", strict_slashes=False)
def about():
    """About page."""
    form = LoginForm(request.form)
    response = make_response(
        render_template(
            "public/about.html",
            form=form,
            local_announcement_type=AnnouncementTypes.ABOUT.value,
            version_from_source=current_app.config[ConfigSettingNames._VERSION_IN_SOURCE.name],
        )
    )
    response.headers.set("Cache-Control", "no-cache")
    return response

@blueprint.route("/race", strict_slashes=False)
def redirect_to_races_page():
    return redirect(url_for('race.show_public_races'))

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

@blueprint.route("/project/tasks/issues.csv")
def tasks_as_issues_csv():
    local_filename = current_app.config[ConfigSettingNames._BUGGY_EDITOR_ISSUES_CSV_FILE.name]
    try:
        response = make_response(
          send_file(
            join_to_project_root(
                current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                local_filename
            )
          )
        )
    except FileNotFoundError as e:
        abort(404)
    response.headers['content-disposition'] = f"attachment; filename=\"{get_download_filename(local_filename)}\""
    return response

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
        task_html = ""
        if current_app.config[ConfigSettingNames.IS_STORING_TASK_LIST_IN_DB.name]:
            task_list_db = DbFile.query.filter_by(
                type=DbFile.TASK_LIST
            ).first()
            if task_list_db is None:
                flash(f"Task list is missing from database: an administrator needs to publish it", "danger")
                abort(404)
            else:
                task_html = task_list_db.contents
        else:
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
    elif page == "report":
        if not current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name]:
            abort(404) # nothing to show if there's no report
        if current_app.config[ConfigSettingNames.PROJECT_REPORT_URL.name]:
            return redirect(current_app.config[ConfigSettingNames.PROJECT_REPORT_URL.name])
        tasks = Task.query.filter_by(is_enabled=True).order_by(
                    Task.phase.asc(),
                    Task.sort_position.asc()
                ).all()
        template = "public/project/report.html"
    elif page == "poster":
        if not is_poster(current_app):
            abort(404) # nothing to show if there's no poster
        if current_app.config[ConfigSettingNames.PROJECT_POSTER_URL.name]:
            return redirect(current_app.config[ConfigSettingNames.PROJECT_POSTER_URL.name])
        template = "public/project/poster.html"
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
    poster_type = current_app.config[ConfigSettingNames.PROJECT_POSTER_TYPE.name]
    is_a_poster = is_poster(current_app)
    if is_report:
        report_link_text = "Report"
        if is_a_poster:
            report_link_text = "Report & Poster"
    elif is_a_poster:
        report_link_text = "Poster"
    else:
        report_link_text = ""
    is_zip_info_displayed = current_app.config[ConfigSettingNames.IS_PROJECT_ZIP_INFO_DISPLAYED.name]
    zip_filename_type = current_app.config[ConfigSettingNames.PROJECT_ZIP_NAME_TYPE.name]
    zip_filename_type_name = None
    zip_filename_example = current_app.config[ConfigSettingNames.USERNAME_EXAMPLE.name]
    is_personalsed_example = current_user and not current_user.is_anonymous
    if zip_filename_type == 'ext_id':
        if current_app.config[ConfigSettingNames.USERS_HAVE_EXT_ID.name]:
            zip_filename_type_name = current_app.config[ConfigSettingNames.EXT_ID_NAME.name]
            if is_personalsed_example:
                zip_filename_example = current_user.ext_id
            if not zip_filename_example:
                zip_filename_example = current_app.config[ConfigSettingNames.EXT_ID_EXAMPLE.name]
                is_personalsed_example = False
        else:
            zip_filename_type = 'username'
    elif zip_filename_type == 'ext_username':
        if current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name]:
            zip_filename_type_name = current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name]
            if is_personalsed_example:
                zip_filename_example = current_user.ext_username
            if not zip_filename_example:
                zip_filename_example = current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name]
                is_personalsed_example = False
    else:
        zip_filename_type = 'username'
    if zip_filename_type == 'username':
        zip_filename_type_name = "race server username"
        if is_personalsed_example:
            zip_filename_example = current_user.username

    submit_deadline=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name]

    return render_template(
        template,
        buggy_editor_repo_url=current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_URL.name],
        editor_local_url=get_buggy_editor_local_url(current_app),
        expected_phase_completion=current_app.config[ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name],
        is_personalsed_example=is_personalsed_example,
        is_poster=is_a_poster,
        is_report=is_report,
        is_showing_project_workflow=current_app.config[ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name],
        is_showing_tech_notes=current_app.config[ConfigSettingNames.IS_SHOWING_TECH_NOTES.name],
        is_storing_texts=current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name],
        is_student_using_repo=current_app.config[ConfigSettingNames.IS_STUDENT_USING_REPO.name],
        is_using_github_api_to_fork=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name],
        is_using_github_api_to_inject_issues=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name],
        is_using_remote_vs_workspace=current_app.config[ConfigSettingNames.IS_USING_REMOTE_VS_WORKSPACE.name],
        is_zip_info_displayed=is_zip_info_displayed,
        poster_type=poster_type,
        project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
        project_remote_server_app_url=current_app.config[ConfigSettingNames.PROJECT_REMOTE_SERVER_APP_URL.name],
        report_type=report_type,
        report_link_text=report_link_text,
        suggested_text_size=current_app.config[ConfigSettingNames.TASK_TEXT_SIZE_SUGGESTION.name],
        site_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
        submission_link=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_LINK.name],
        submit_deadline=submit_deadline,
        submit_deadline_day=get_day_of_week(submit_deadline),
        superbasics_url=current_app.config[ConfigSettingNames.SUPERBASICS_URL.name],
        tasks=tasks,
        validation_task=current_app.config[ConfigSettingNames.TASK_NAME_FOR_VALIDATION.name],
        vcs_name=current_app.config[ConfigSettingNames.VCS_NAME.name],
        workflow_url=current_app.config[ConfigSettingNames.PROJECT_WORKFLOW_URL.name],
        zip_filename_example=zip_filename_example,
        zip_filename_type_name=zip_filename_type_name,
        zip_filename_type=zip_filename_type,
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
    if not current_app.config[ConfigSettingNames.IS_SHOWING_TECH_NOTES.name]:
        flash("This race server is not displaying tech notes", "warning")
        abort(404)
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

@blueprint.route("/editor/download", strict_slashes=False)
def download_editor_zip():
    if current_app.config[ConfigSettingNames.IS_USING_VCS.name]:
        flash("Cannot download editor source files from this race server", "warning")
        abort(404)
    if zip_url := current_app.config[ConfigSettingNames.EDITOR_DOWNLOAD_URL.name]:
        return redirect(zip_url)
    zipfile = join_to_project_root(
        current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
        current_app.config[ConfigSettingNames._EDITOR_OUTPUT_DIR.name],
        current_app.config[ConfigSettingNames.EDITOR_ZIPFILE_NAME.name]
    )
    if not path.exists(zipfile):
        flash(
            "Editor zip file not available (either you can't download it from"
            " this server, or admin has not published it yet)",
            "danger")
        abort(404)
    return send_file(zipfile)