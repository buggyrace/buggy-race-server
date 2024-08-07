# -*- coding: utf-8 -*-
"""Admin views/controllers
   (except for races/racetracks — those are in admin/views_races.py)
"""
import csv
import json
import io  # for CSV dump
import random  # for API tests
from datetime import datetime, timedelta, timezone
import os
from collections import defaultdict
import markdown
import re
import subprocess

from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    Response,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import bindparam, select, insert, update

from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

from buggy_race_server.admin.forms import (
    AnnouncementActionForm,
    AnnouncementForm,
    ApiKeyForm,
    BulkRegisterForm,
    EnableDisableLoginsForm,
    GeneralSubmitForm,
    GenerateTasksForm,
    PublishEditorSourceForm,
    SettingForm,
    SetupAuthForm,
    SetupSettingForm,
    SimpleStringForm,
    SubmitWithConfirmForm,
    SubmitWithConfirmAndAuthForm,
    TaskForm,
    UploadTaskTextsForm,
    UserTypesForLogin,
)
from buggy_race_server.admin.models import (
    Announcement,
    DbFile,
    DistribMethods,
    TaskText,
    Setting,
    SocialSetting,
    Task
)
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.buggy.views import show_buggy as show_buggy_by_user
from buggy_race_server.buggy.views import delete_buggy as delete_buggy_by_user
from buggy_race_server.config import (
    AnnouncementTypes,
    ConfigGroupNames,
    ConfigSettingNames,
    ConfigSettings,
    ConfigTypes
)
from buggy_race_server.database import db
from buggy_race_server.extensions import csrf, bcrypt
from buggy_race_server.user.forms import UserForm, RegisterForm, UserCommentForm
from buggy_race_server.user.models import User
from buggy_race_server.utils import (
    _get_buggy_editor_kwargs,
    admin_only,
    create_default_task_markdown_file,
    create_editor_zipfile,
    flash_errors,
    get_day_of_week,
    get_download_filename,
    get_flag_color_css_defs,
    get_pretty_approx_duration,
    get_tasks_as_issues_csv,
    join_to_project_root,
    load_config_setting,
    load_settings_from_db,
    load_tasks_into_db,
    most_recent_timestamp,
    prettify_form_field_name,
    publish_task_list,
    publish_tasks_as_issues_csv,
    publish_tech_notes,
    quote_string,
    redact_password_in_database_url,
    refresh_global_announcements,
    servertime_str,
    set_and_save_config_setting,
    staff_only,
    stringify_datetime,
)

blueprint = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
  static_folder="../static"
)

SETTING_PREFIX = "settings" # the name of settings subform

def _is_from_dashboard():
    if ref := request.referrer:
        return ref.endswith("/admin/") or ref.endswith("/admin")
    return False

def _is_task_list_published():
    task_list_fname = current_app.config[ConfigSettingNames._TASK_LIST_HTML_FILENAME.name]
    return task_list_fname and os.path.exists(
        join_to_project_root(
            current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
            task_list_fname
        )
    )

def _is_tech_notes_index_published():
    return os.path.exists(
        join_to_project_root(
            current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
            current_app.config[ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name],
            current_app.config[ConfigSettingNames._TECH_NOTES_PAGES_DIR.name],
            "index.html"
        )
    )

def _is_editor_zipfile_published():
    return os.path.exists(
        join_to_project_root(
            current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
            current_app.config[ConfigSettingNames._EDITOR_OUTPUT_DIR.name],
            current_app.config[ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name]
        )
    )

def _save_read_del_csv(csv_file):
    lines = None
    err_msgs = []
    if csv_file.filename:
        csv_filename_with_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            secure_filename(csv_file.filename)
        )
        csv_file.save(csv_filename_with_path)
        try:
            with open(csv_filename_with_path) as uploaded_file:
                lines = uploaded_file.readlines()
        except Exception as e:
            err_msgs.append(f"Error reading CSV file: {e}")
        try:
            os.unlink(csv_filename_with_path)
        except os.error as e:
            err_msgs.append(f"Problem deleting uploaded file: {e}")
    return (lines, err_msgs)

def _update_settings_in_db(form):
    """ Used by setup and settings: returns boolean success.
        Check the form has validated OK *before* calling this.
    """
    settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
    config_data_insert = []
    config_data_update = []
    qty_settings_changed = 0
    has_changed_secret_key = False
    is_in_setup_mode = bool(current_app.config[ConfigSettingNames._SETUP_STATUS.name])
    is_update_ok = True # optimistic
    for setting_form in form.settings.data:
        name = setting_form.get('name').upper() # force uppercase for config keys
        value = setting_form.get('value').strip()
        if ConfigSettings.TYPES.get(name) == ConfigTypes.PASSWORD:
            value = bcrypt.generate_password_hash(value).decode('utf8')
        is_changed_value = False
        if name in settings_as_dict:
            if settings_as_dict[name] != value:
                if ConfigSettings.TYPES.get(name) in [ConfigTypes.PASSWORD, ConfigTypes.SENSITIVE_STRING]:
                    changed_msg = f"Changed {name} to a new value"
                else:
                    pretty_old = ConfigSettings.prettify(name, settings_as_dict[name])
                    pretty_new = ConfigSettings.prettify(name, value)
                    changed_msg = f"Changed {name} from \"{pretty_old}\" to \"{pretty_new}\""
                flash(changed_msg, "info")
                config_data_update.append({
                    "name": name,
                    "value": value
                })
                is_changed_value = True
        else:
            # config not in settings table: unexpected but roll with it: INSERT
            if ConfigSettings.TYPES.get(name) == ConfigTypes.PASSWORD:
                changed_msg = f"Setting {name}\""
            else:
                changed_msg = f"Setting {name} to \"{ConfigSettings.prettify(name, value)}\""
            flash(changed_msg, "info")
            config_data_insert.append({
                "id": name,
                "value": value
            })
            is_changed_value = True
        if is_changed_value:
            qty_settings_changed += 1
            has_changed_secret_key = name == ConfigSettingNames.SECRET_KEY.name
    if qty_settings_changed:
        settings_table = Setting.__table__
        if config_data_update:
            try:
              result = db.session.execute(
                update(settings_table)
                  .where(settings_table.c.id == bindparam("name"))
                  .values(value=bindparam("value")),
                  config_data_update
              )
              db.session.commit()
            except Exception as e:
                flash(str(e), "danger")
                is_update_ok = False
        if config_data_insert:
            try:
              result = db.session.execute(
                  insert(settings_table),
                  config_data_insert
              )
              db.session.commit()
            except Exception as e:
                flash(str(e), "danger")
                is_update_ok = False
        # we've changed config, try to update config too
        load_settings_from_db(current_app)
        if has_changed_secret_key:
            # this is problematic: because the existing token will now fail
            # as well as any existing sessions probably
            # so this isn't really recommended
            csrf.init_app(current_app)
        if (
          not is_in_setup_mode
          and current_app.config[ConfigSettingNames.IS_SHOWING_RESTART_SUGGESTION.name]
        ):
            flash(
              "When you've finished changing settings, "
              "it's a good idea to restart the server", "info"
            )
    else:
        flash("OK, no settings were changed", "info")
    return is_update_ok

def _user_summary(username_list):
    if len(username_list) == 1:
        return f"user '{username_list[0]}'"
    else:
        return f"{len(username_list)} users"

def _csv_tidy_string(row, fieldname, want_lower=False):
  # incoming CSV fields might be None (i.e., not "")
  # e.g. if the row wasn't long enough
  s = row[fieldname] if fieldname in row else None
  if s is not None:
      s = str(s).strip()
      if want_lower:
          s = s.lower()
  return s

def _flash_errors(form):
  """ Flash errors in form, which may include settings subform """
  # if hasattr(form, SETTING_PREFIX) and form.settings.errors:
  #   for setting_error in form.settings.errors:
  #     for field in setting_error:
  #       pass 
  for fieldName, errorMessages in form.errors.items():
      for err_msg in errorMessages:
          if isinstance(err_msg, dict):
              for field in err_msg: # field is always "value"
                flash(f"{err_msg[field][0]}", "danger")
          else:
              flash(
                f"{prettify_form_field_name(fieldName)}: {err_msg}",
                "danger"
              )

def setup_summary():
    """ If setup is complete, this summarises the current config and db state,
    and unlike the dashboard has some helpful suggestions as to what to do next."""
    if (
      not current_user
      or not current_user.is_authenticated
      or not current_user.is_staff
    ):
        abort(403)
    if ConfigSettingNames._SETUP_STATUS.name in session:
        del session[ConfigSettingNames._SETUP_STATUS.name]
    user_fields_dict = ConfigSettings.users_additional_fieldnames_is_enabled_dict(current_app)
    pretty_user_fields = ".".join(
      User.tidy_fieldnames(
        [
          fieldname for fieldname in user_fields_dict
          if user_fields_dict[fieldname]
        ]
      )
    )
    institution_home_url = current_app.config[ConfigSettingNames.INSTITUTION_HOME_URL.name]
    report_type = current_app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name]
    qty_announcements_global = 0
    qty_announcements_login = 0
    qty_announcements_tagline = 0
    for ann in current_app.config[ConfigSettingNames._CURRENT_ANNOUNCEMENTS.name]:
        if ann.type == AnnouncementTypes.LOGIN.value:
            qty_announcements_login += 1
        elif ann.type == AnnouncementTypes.TAGLINE.value:
            qty_announcements_tagline += 1
        else:
            qty_announcements_global += 1
    buggy_editor_repo_owner=current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_OWNER.name]
    api_secret_ttl_pretty=get_pretty_approx_duration(current_app.config[ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name])
    return render_template(
      "admin/setup_summary.html",
      is_using_github=current_app.config[ConfigSettingNames.IS_USING_GITHUB.name],
      buggy_editor_download_url=current_app.config[ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name],
      is_editor_zipfile_published=_is_editor_zipfile_published(),
      editor_zip_generated_datetime=current_app.config[ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name],
      buggy_editor_source_commit=current_app.config[ConfigSettingNames._BUGGY_EDITOR_SOURCE_COMMIT.name],
      buggy_editor_origin_github_url=current_app.config[ConfigSettingNames._BUGGY_EDITOR_ORIGIN_GITHUB_URL.name],
      api_secret_ttl_pretty=api_secret_ttl_pretty,
      buggy_editor_repo_owner=buggy_editor_repo_owner,
      buggy_editor_github_url=current_app.config[ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name],
      institution_full_name=current_app.config[ConfigSettingNames.INSTITUTION_FULL_NAME.name],
      institution_home_url=institution_home_url,
      institution_short_name=current_app.config[ConfigSettingNames.INSTITUTION_SHORT_NAME.name],
      is_api_secret_otp=current_app.config[ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name],
      is_default_repo_owner=buggy_editor_repo_owner == 'buggyrace', # the default owner
      is_report=bool(report_type),
      is_showing_project_workflow=current_app.config[ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name],
      is_student_api_otp_allowed=current_app.config[ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name],
      is_student_using_github_repo=current_app.config[ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name],
      is_task_list_published=_is_task_list_published(),
      is_tech_notes_index_published=_is_tech_notes_index_published(),
      is_tech_note_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
      is_using_github_api_to_fork=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name],
      is_using_github_api_to_inject_issues=current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name],
      pretty_institution_home_url=re.sub(r"^https?://", "", institution_home_url),
      pretty_user_fields=pretty_user_fields,
      project_code=current_app.config[ConfigSettingNames.PROJECT_CODE.name],
      project_phase_min_target=current_app.config[ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name],
      qty_announcements_global=qty_announcements_global,
      qty_announcements_login=qty_announcements_login,
      qty_announcements_tagline=qty_announcements_tagline,
      qty_students=User.query.filter_by(is_active=True, is_student=True).count(),
      qty_tasks=Task.query.filter_by(is_enabled=True).count(),
      qty_users=User.query.filter_by(is_active=True).count(),
      report_type=report_type,
      server_time=datetime.now(current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name]).strftime('%Y-%m-%d %H:%M:%S %Z (%z)'),
      submission_deadline=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name],
      submission_link=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_LINK.name],
      task_list_published_at=current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
      tasks_loaded_at=current_app.config[ConfigSettingNames._TASKS_LOADED_DATETIME.name],
      tech_notes_external_url=current_app.config[ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name],
      tech_notes_published_at=current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name],
      workflow_url=current_app.config[ConfigSettingNames.PROJECT_WORKFLOW_URL.name],
    )

@blueprint.route("/setup", methods=["GET", "POST"], strict_slashes=False)
def setup():
    # always get setup status from database during setup:
    setup_status = load_config_setting(current_app, ConfigSettingNames._SETUP_STATUS.name)
    if not setup_status:
        return setup_summary()
    try:
        setup_status_from_session = int(session.get(ConfigSettingNames._SETUP_STATUS.name) or 0)
    except ValueError():
        setup_status_from_session = 0
    if setup_status_from_session:
        if setup_status < setup_status_from_session:
            flash("Unexpected session bump: clearing your session status", "warning")
            del session[ConfigSettingNames._SETUP_STATUS.name]
    if setup_status > setup_status_from_session + 1:
        flash("Cannot continue setup in this session (maybe someone else is already setting up?)", "warning")
        abort(403)
    qty_setup_steps = len(ConfigSettings.SETUP_GROUPS)
    if setup_status == 1:
        form = SetupAuthForm(request.form)
        # here we grant this session (effectively, this user) setup status
        session[ConfigSettingNames._SETUP_STATUS.name] = setup_status
    else:
        # after initial setup (auth), user must be logged in
        if current_user.is_anonymous or not current_user.is_administrator:
            admins = ", ".join([u.username for u in User.query.filter_by(access_level=User.ADMINISTRATOR)])
            flash(f"Setup is not complete: you must log in as an admin user ({admins}) to continue", "warning")
            if not current_user.is_anonymous:
                logout_user()
            return redirect( url_for('public.login'))
        form = SetupSettingForm(request.form)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if setup_status == 1: # this updating auth and creating a new admin user
                set_and_save_config_setting(
                  current_app,
                  ConfigSettingNames.AUTHORISATION_CODE.name,
                  bcrypt.generate_password_hash(form.new_auth_code.data).decode('utf8')
                )
                new_admin_username = form.admin_username.data.strip().lower()
                if admin_user := User.query.filter_by(username=new_admin_username).first():
                    # if this user is not an admin, need to promote them:
                    if admin_user.access_level != User.ADMINISTRATOR:
                        admin_user.access_level=User.ADMINISTRATOR
                        admin_user.save()
                        flash(f"Promoted user {new_admin_username} to administrator")
                    admin_user.set_password(form.admin_password.data)
                    flash(f"Updated existing user {new_admin_username}'s password", "warning")
                else:
                    admin_user = User.create(
                        username=new_admin_username,
                        password=form.admin_password.data,
                        access_level=User.ADMINISTRATOR,
                        comment=f"First admin user, created during setup :-)",
                    )
                    flash(f"Created new admin user \"{new_admin_username}\"", "info")
                admin_user.is_active = True
                admin_user.is_student = False
                admin_user.save()
                setup_status += 1
                set_and_save_config_setting(
                    current_app,
                    ConfigSettingNames._SETUP_STATUS.name,
                    setup_status
                )
                login_user(admin_user)
                admin_user.logged_in_at = datetime.now(timezone.utc)
                admin_user.first_logged_in_at = admin_user.logged_in_at
                admin_user.save()
                flash(f"OK, you're logged in with admin username \"{new_admin_username}\"", "success")
            else: # handle a regular settings update, which may also be part of setup
                if _update_settings_in_db(form):
                  setup_status += 1
                  set_and_save_config_setting(
                      current_app,
                      ConfigSettingNames._SETUP_STATUS.name,
                      setup_status
                  )
                  # here we grant this session setup status
                  session[ConfigSettingNames._SETUP_STATUS.name] = setup_status
                else:
                    # something wasn't OK, so don't save and move on
                    # (the errors will have been explicitly flashed)
                    pass
        else:
            _flash_errors(form)
    if setup_status > qty_setup_steps:
        setup_status = 0
        set_and_save_config_setting(
          current_app,
          ConfigSettingNames._SETUP_STATUS.name,
          setup_status
        )
        flash("Setup complete: you can now publish tech notes, add/edit tasks, and register users", "success")
        return setup_summary()
    group_name = ConfigSettings.SETUP_GROUPS[setup_status-1]
    settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
    html_descriptions = { 
        setting: markdown.markdown(ConfigSettings.DESCRIPTIONS[setting])
        for setting in ConfigSettings.DESCRIPTIONS
    }
    social_settings = SocialSetting.get_socials_from_config(
        settings_as_dict, want_all=True
    )
    pretty_group_name_dict = { 
        name:ConfigSettings.pretty_group_name(name)
        for name in ConfigSettings.GROUPS
    }
    return render_template(
        "admin/setup.html",
        env_setting_overrides=current_app.config[ConfigSettings.ENV_SETTING_OVERRIDES_KEY],
        form=form,
        group_name=group_name,
        groups=ConfigSettings.GROUPS,
        html_descriptions=html_descriptions,
        pretty_default_settings=ConfigSettings.get_pretty_defaults(),
        pretty_group_name_dict=pretty_group_name_dict,
        qty_setup_steps=qty_setup_steps,
        SETTING_PREFIX=SETTING_PREFIX,
        settings=settings_as_dict,
        setup_group_description=ConfigSettings.SETUP_GROUP_DESCRIPTIONS[group_name],
        setup_status=setup_status,
        social_settings=social_settings,
        sorted_groupnames=[name for name in ConfigSettings.SETUP_GROUPS],
        type_of_settings=ConfigSettings.TYPES,
  )

@blueprint.route("/", strict_slashes=False)
@login_required
@staff_only
def admin():
    TASK_NOTE_LENGTH_THRESHOLD = 2 # texts shorter than this are not counted
    today = datetime.now(timezone.utc).date()
    one_week_ago = today - timedelta(days=7)
    users = User.query.order_by(User.username).all()
    buggies = Buggy.query.join(User).filter(
                User.is_student==True
              ).filter(User.is_active==True).all()
    students_active = [s for s in users if s.is_student and s.is_active]
    students_never_logged_in = [s for s in students_active if s.logged_in_at is None ]
    students_logged_in_ever = [s for s in students_active if s not in students_never_logged_in]
    students_logged_in_today = [s for s in students_logged_in_ever if s.logged_in_at.date() >= today]
    students_logged_in_this_week = [s for s in students_logged_in_ever
                                        if s not in students_logged_in_today
                                        and s.logged_in_at.date() >= one_week_ago
                                    ]
    students_logged_in_ever = [s for s in students_logged_in_ever if s.logged_in_at.date() < one_week_ago ]
    students_uploaded_this_week = [s for s in students_active if s.uploaded_at and s.uploaded_at.date() >= one_week_ago]
    users_deactivated = [u for u in users if not u.is_active]
    staff_users = [u for u in users if u.is_active and u.is_staff]
    other_users = [u for u in users if u.is_active and not (u in students_active or u in staff_users)]
    tasks = Task.query.filter_by(is_enabled=True).order_by(Task.phase.asc(), Task.sort_position.asc()).all()
    qty_tasks = len(tasks)
    tasks_by_id = {task.id: task.fullname for task in tasks}
    qty_texts_by_task = defaultdict(int)
    qty_texts = 0
    if is_storing_texts := current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        texts = TaskText.query.join(User).filter(
            User.is_student==True).filter(User.is_active==True
        ).all()
        qty_texts = len(texts)
        for text in texts:
            if len(text.text) > TASK_NOTE_LENGTH_THRESHOLD:
                qty_texts_by_task[tasks_by_id[text.task_id]] += 1

    submission_deadline=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name]
    return render_template(
        "admin/dashboard.html",
        form=GeneralSubmitForm(), # for publish submit buttons
        is_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
        is_storing_texts=is_storing_texts,
        is_task_list_published=_is_task_list_published(),
        is_tech_notes_index_published=_is_tech_notes_index_published(),
        is_editor_zipfile_published=_is_editor_zipfile_published(),
        is_using_github=current_app.config[ConfigSettingNames.IS_USING_GITHUB.name],
        buggy_editor_download_url=current_app.config[ConfigSettingNames.BUGGY_EDITOR_DOWNLOAD_URL.name],
        notes_generated_timestamp=servertime_str(
          current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
          current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name]
        ),
        other_users=other_users,
        purge_form = GeneralSubmitForm(),
        qty_buggies=len(buggies),
        qty_other_users=len(other_users),
        qty_staff_users=len(staff_users),
        qty_students_active=len(students_active),
        qty_students_logged_in_this_week=len(students_logged_in_this_week),
        qty_students_logged_in_today=len(students_logged_in_today),
        qty_students_logged_in_ever=len(students_logged_in_ever),
        qty_students_never_logged_in=len(students_never_logged_in),
        qty_students=len(students_active),
        qty_tasks=qty_tasks,
        qty_texts_by_task=qty_texts_by_task,
        qty_texts=qty_texts,
        qty_uploads_today=len([s for s in students_uploaded_this_week if s.uploaded_at.date() >= today]),
        qty_uploads_week=len(students_uploaded_this_week),
        qty_users_deactivated=len(users_deactivated),
        qty_users=len(users),
        staff_users=staff_users,
        students_active = students_active,
        students_logged_in_this_week=students_logged_in_this_week,
        students_logged_in_today=students_logged_in_today,
        students_logged_in_ever=students_logged_in_ever,
        students_never_logged_in=students_never_logged_in,
        submission_deadline=submission_deadline,
        submit_deadline_day=get_day_of_week(submission_deadline),
        tasks=tasks,
        task_list_updated_timestamp=current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
        tech_notes_generated_at=current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name],
        unexpected_config_settings=current_app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY],
        users_deactivated=users_deactivated,
    )

@blueprint.route("/users", strict_slashes=False)
@blueprint.route("/users/<data_format>")
@login_required
@staff_only
def list_users(data_format=None, want_detail=True):
    """Admin list-of-uses/students page (which is the admin home page too)."""
    users = User.query.all()
    users = sorted(users, key=lambda user: (user.is_staff, user.username))
    students = [s for s in users if s.is_student]
    qty_teaching_assistants = len([u for u in users if u.is_teaching_assistant])
    admin_usernames = [user.username for user in users if user.is_administrator]
    qty_admins = len(admin_usernames)
    if data_format == "csv": # note: CSV is only students
        si = io.StringIO()
        cw = csv.writer(si)
        # To get the column names, use the current_user (admin) even though
        # we're not going to save the data (there might not be any students)
        cw.writerow(current_user.get_fields_as_dict_for_csv().keys())
        for s in students:
            cw.writerow(list(s.get_fields_as_dict_for_csv().values()))
        filename = get_download_filename("users.csv", want_datestamp=True)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv"
        return output
    else:
        # TODO want_detail shows all users (otherwise it's only students)
        current_user_can_edit = current_user.is_administrator
        edit_method = "admin.edit_user"
        if (
            current_user.is_teaching_assistant and
            current_app.config[ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name]
        ):
            current_user_can_edit = True
            edit_method = "admin.edit_user_comment"
        is_showing_github_column = (
            current_app.config[ConfigSettingNames.IS_USING_GITHUB.name]
            and
            current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name]
        )
        return render_template("admin/users.html",
            admin_usernames=admin_usernames,
            current_user_can_edit=current_user_can_edit,
            edit_method=edit_method,
            editor_repo_name=current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name],
            ext_id_name=current_app.config[ConfigSettingNames.EXT_ID_NAME.name],
            ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
            ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
            is_demo_server=current_app.config[ConfigSettingNames._IS_DEMO_SERVER.name],
            is_password_change_by_any_staff=current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name],
            is_showing_github_column=is_showing_github_column,
            qty_admins=qty_admins,
            qty_students_login_enabled=len([s for s in students if s.is_login_enabled]),
            qty_students_enabled=len([s for s in students if s.is_active]),
            qty_students_github=len([s for s in students if s.github_username]),
            qty_students_logged_in=len([s for s in students if s.logged_in_at]),
            qty_students_uploaded_json=len([s for s in students if len(s.latest_json)>1]),
            qty_students_logged_in_first=len([s for s in students if s.first_logged_in_at]),
            qty_students=len(students),
            qty_teaching_assistants=qty_teaching_assistants,
            users=users,
            want_detail=want_detail,
        )

@blueprint.route("/users/register", methods=["GET", "POST"], strict_slashes=False)
@blueprint.route("/users/register/<data_format>", methods=["POST"])
@login_required
@admin_only
def bulk_register(data_format=None):
    """Register multiple users."""
    is_json = data_format == "json"
    err_msgs = []
    form = BulkRegisterForm(request.form)
    if form.is_submitted() and form.validate():
        delete_path = None
        lines = []
        if "csv_file" in request.files:
            csv_file = request.files['csv_file']
            if csv_file.filename:
                csv_filename_with_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    secure_filename(csv_file.filename)
                )
                csv_file.save(csv_filename_with_path)
                delete_path = csv_filename_with_path
                try:
                    with open(csv_filename_with_path) as uploaded_file:
                      lines = uploaded_file.readlines()
                except Exception as e:
                    err_msgs.append(f"Error reading CSV file: {e}", "danger")
        else:
            lines = form.userdata.data.splitlines()
        if len(lines):
            lines[0] = ",".join(User.tidy_fieldnames(lines[0].split(",")))
        reader = csv.DictReader(lines, delimiter=',')
        qty_users = 0
        line_no = 0
        problem_lines = []
        clean_user_data = []
        if len(lines) < 2:
            err_msgs.append("Need CSV with a header row, then at least one line of data")
        elif missing := User.get_missing_fieldnames(reader.fieldnames):
            err_msgs.append(f"CSV header row is missing some required fields: {', '.join(missing)}")
        else:
            usernames = []
            for row in reader:
                line_no += 1
                username = row['username'].strip().lower() if 'username' in row else None
                if username is not None:
                    usernames.append(username)
                new_user = User(
                    username=username,
                    ext_id=row['ext_id'].strip() if 'ext_id' in row else None,
                    ext_username=row['ext_username'].strip().lower() if 'ext_username' in row else None,
                    email=_csv_tidy_string(row, 'email', want_lower=True),
                    password=_csv_tidy_string(row, 'password', want_lower=False),
                    first_name=_csv_tidy_string(row, 'first_name', want_lower=False),
                    last_name=_csv_tidy_string(row, 'last_name', want_lower=False),
                    created_at=datetime.now(timezone.utc),
                    is_active=True,
                    is_student=True,
                    access_level=User.NO_STAFF_ROLE, # to convert to staff, must edit
                    latest_json="",
                    comment=_csv_tidy_string(row, 'comment', want_lower=False),
                    is_api_secret_otp=current_app.config[ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name],
                )
                #current_app.logger.info("{}, pw:{}".format(username, password))
                if new_user.password and len(new_user.password) >= 4: # passwords longer than 4
                    qty_users += 1
                    clean_user_data.append(new_user.get_fields_as_dict_for_insert())
                else:
                    problem_lines.append(line_no)
            if len(problem_lines) > 0:
                pl = "s" if len(problem_lines)>1 else ""
                line_nos = ", ".join(map(str,problem_lines))
                err_msgs.append(f"Bulk registration aborted with {len(problem_lines)} problem{pl}: see line{pl}: {line_nos}")
            else:
              try:
                result = db.session.execute(
                    insert(User.__table__),
                    clean_user_data
                )
                db.session.commit()
              except Exception as e:
                  # risky but frustratingly no easy way to get the specific database
                  # error as it's coming back from the connection: e.g.,
                  # (mysql.connector.errors.IntegrityError) 1062 (23000): Duplicate entry 'aaaa' for key 'username'
                  ex_str = str(e).split("\n")[0] # mySQL sends the SQL back too after a newline: don't want
                  # for JSON, users are being updated one user(name) at a time
                  bad_username = f"\"{usernames[0]}\": " if len(usernames) == 1 else ""
                  err_msgs.append(f"{bad_username}{ex_str}")
              if not is_json:
                   flash(f"Bulk registered {qty_users} users", "warning")
        if delete_path:
            try:
                os.unlink(delete_path)
            except os.error as e:
                err_msgs.append(f"Problem deleting uploaded file: {e}")
        if is_json:
            if err_msgs:
                payload = {
                  'status': "error",
                  'error': err_msgs[0],
                  'errors': err_msgs
                }
            else:
                payload = {"status": "OK"}
            return jsonify(payload)
        else:
            for err_msg in err_msgs:
                flash(err_msg, "danger")
    else:
        if is_json:
          errors = []
          for err_key in form.errors:
              errors.append(form.errors[err_key])
          return jsonify({
              "status": "error",
              "error": errors[0],
              "errors": errors
          })
        else:
            flash_errors(form)
    csv_fieldnames = ['username', 'password'] + ConfigSettings.users_additional_fieldnames(current_app)
    return render_template(
        "admin/users_register.html",
        csv_fieldnames=f"{csv_fieldnames} {current_app.config}",
        docs_url=current_app.config[ConfigSettingNames._BUGGY_RACE_DOCS_URL.name],
        example_csv_data = [
            ",".join(csv_fieldnames),
            ",".join(User.get_example_data("ada", csv_fieldnames)),
            ",".join(User.get_example_data("chaz", csv_fieldnames)),
        ],
        form=form,
    )

@blueprint.route("/user/<user_id>", methods=['GET'])
@login_required
@staff_only
def show_user(user_id):
    if str(user_id).isdigit():
        user = User.get_by_id(int(user_id))
    else:
        user = User.query.filter_by(username=user_id).first()
    if user is None:
        abort(404)
    texts_by_task_id=TaskText.get_dict_texts_by_task_id(user.id)
    return  render_template(
        "admin/user.html",
        user=user,
        api_form=ApiKeyForm(),
        is_demo_server=current_app.config[ConfigSettingNames._IS_DEMO_SERVER.name],
        is_own_text=user.id == current_user.id,
        tasks_by_phase=Task.get_dict_tasks_by_phase(want_hidden=False),
        texts_by_task_id=texts_by_task_id,
        qty_texts=len(texts_by_task_id),
        ext_id_name=current_app.config[ConfigSettingNames.EXT_ID_NAME.name],
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
        is_password_change_by_any_staff=current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name],
        upload_text_form=UploadTaskTextsForm(),
    )

def manage_user(user_id):
  is_registering_new_user = user_id is None
  if is_registering_new_user:
      user = None
      action_url=url_for('admin.new_user')
      form=RegisterForm(request.form)
  else:
      if str(user_id).isdigit():
          user = User.get_by_id(int(user_id))
      else:
          user = User.query.filter_by(username=user_id).first()
      if user is None:
          flash("No such user", "info")
          abort(404)
      action_url=url_for('admin.edit_user', user_id=user.id)
      form = UserForm(request.form, obj=user, app=current_app)
  if request.method == "POST":
      if form.is_submitted() and form.validate():
          username = form.username.data.lower()
          if is_registering_new_user:
              user = User(
                  username=username,
                  password=form.password.data,
                )
          user.username = username # validation catches non-unique usernames
          user.comment = form.comment.data
          user.is_student = form.is_student.data
          user.is_active = form.is_active.data
          user.is_login_enabled = form.is_login_enabled.data
          user.is_demo_user = form.is_demo_user.data if form.is_demo_user is not None else False
          if current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
              user.first_name = form.first_name.data
          if current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name]:
              user.last_name = form.last_name.data
          if current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name]:
              user.email = form.email.data
          if current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name]:
              user.ext_username = form.ext_username.data
          if current_app.config[ConfigSettingNames.USERS_HAVE_EXT_ID.name]:
              user.ext_id = form.ext_id.data
          if not is_registering_new_user:
              if form.access_level.data > user.access_level:
                  flash(f"Promoted user to {User.ROLE_NAMES[form.access_level.data]}", "info")
              elif form.access_level.data < user.access_level:
                  flash(f"Demoted user to {User.ROLE_NAMES[form.access_level.data]}", "info")
          user.access_level = form.access_level.data
          user.is_api_secret_otp=current_app.config[ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name]
          user.save()
          if is_registering_new_user:
              success_msg = f"OK, registered new user {user.pretty_username}"
          else:
              success_msg = f"OK, updated user {user.pretty_username}"
          if current_user.is_anonymous or not current_user.is_administrator:
              return_url = url_for("public.login")
          else:
              return_url = url_for("admin.list_users")
          flash(success_msg, "success")
          return redirect(return_url)
      else:
        flash_errors(form)
        if is_registering_new_user:
            flash("Did not register new user", "danger")
        else:
            flash(f"Did not update user {user.pretty_username}", "danger")
  is_current_user_comment_editor = (not current_user.is_anonymous) and (
        current_user.is_administrator or 
        (current_user.is_teaching_assistant and current_app.config[ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name])
  )
  return render_template(
      "admin/user_edit.html",
      action_url=action_url,
      example_username=current_app.config[ConfigSettingNames.USERNAME_EXAMPLE.name],
      ext_id_name=current_app.config[ConfigSettingNames.EXT_ID_NAME.name],
      ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
      ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
      form=form,
      is_current_user_comment_editor=is_current_user_comment_editor,
      is_demo_server=current_app.config[ConfigSettingNames._IS_DEMO_SERVER.name],
      is_registration_allowed=current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name],
      user=user,
  )

@blueprint.route("/users/logins", methods=['GET', 'POST'], strict_slashes=False)
@login_required
@admin_only
def enable_or_disable_logins():
    # UserTypesForLogin
    form = EnableDisableLoginsForm(request.form)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if form.user_type.data == UserTypesForLogin.students.name:
                base_query = select(User).filter(User.is_student == True).with_only_columns(User.id)
                user_str = "all students"
            elif form.user_type.data == UserTypesForLogin.teaching_assistants.name:
                base_query = select(User).filter(User.access_level == User.TEACHING_ASSISTANT).with_only_columns(User.id)
                user_str = "all TAs"
            else:
                base_query = select(User).with_only_columns(User.id)
                user_str = "everybody"
            try:
                # note: would prefer to include synchronize_session='fetch'
                db.session.execute(
                    update(User).where(User.id.in_(base_query))
                    .values(is_login_enabled=bool(form.submit_enable.data))
                )
                db.session.commit()
            except Exception as e:
                flash(str(e), "danger")
            else:
                flash(
                    f"OK, enabled logins for {user_str}" if form.submit_enable.data
                    else f"OK, disabled logins for {user_str}",
                    "info"
                )
                return redirect(url_for("admin.list_users"))
        else:
            flash_errors(form)
    return render_template(
        "admin/user_logins.html",
        form=form
    )

# user_id may be username or id
@blueprint.route("/user/<user_id>/delete-github", methods=['POST'])
@login_required
@admin_only
def delete_github_details(user_id):
    if str(user_id).isdigit():
        user = User.get_by_id(int(user_id))
    else:
        user = User.query.filter_by(username=user_id).first()
    if user is None:
        abort(404)
    form = SubmitWithConfirmForm(request.form)
    if form.is_submitted() and form.validate():
        if (user.github_username is None and user.github_access_token is None):
            flash("Nothing changed: user's GitHub details were already removed", "warning")
        elif not form.is_confirmed.data:
            flash(
              f"Did not not delete GitHub details because you did not explicity confirm it",
              "danger"
            )
            return redirect(url_for("admin.edit_user", user_id=user.id))
        else:
            user.github_username = None
            user.github_access_token = None
            user.save()
            flash(
              f"OK, user {user.pretty_username}'s GitHub details have been removed",
              "success"
            )
            flash(
              "Reminder: this hasn't changed anything on GitHub.com — "
              "if they forked the buggy editor repo, it will still be there",
              "info"
            )
    return redirect(url_for("admin.list_users"))

@blueprint.route("/users/new", methods=['GET', 'POST'])
def new_user():
    is_registration_allowed=current_app.config[ConfigSettingNames.IS_PUBLIC_REGISTRATION_ALLOWED.name]
    if not (
        is_registration_allowed or
        (not current_user.is_anonymous and current_user.is_administrator)
      ):
        flash("You need to be an administrator to register new users (registration is not public)", "warning")
        abort(403)
    return manage_user(user_id=None)

@blueprint.route("/user/<user_id>/edit-comment", methods=['GET', 'POST'])
@login_required
@staff_only
def edit_user_comment(user_id):
    if not(
        current_user.is_administrator or
        (
          current_user.is_teaching_assistant and
          current_app.config[ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name]
        )
    ):
        abort(403)
    if str(user_id).isdigit():
        user = User.get_by_id(int(user_id))
    else:
        user = User.query.filter_by(username=user_id).first()
    if user is None:
        flash("No such user", "danger")
        abort(404)
    form = UserCommentForm(request.form, obj=user)
    if request.method=="POST":
        if form.is_submitted() and form.validate():
            user.comment = form.comment.data.strip()
            user.save()
            flash(f"OK, updated comment on user {user.pretty_username}", "success")
            return redirect(url_for("admin.show_user", user_id=user_id))
        else:
          flash("Did not update comment!", "danger")
          flash_errors(form)
    return render_template(
      "admin/user_edit_comment.html",
      user=user,
      form=form,
      is_ta_edit_comment_enabled=current_app.config[ConfigSettingNames.IS_TA_EDIT_COMMENT_ENABLED.name],
      is_ta_password_change_enabled=current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name],
      is_ta_set_api_key_enabled=current_app.config[ConfigSettingNames.IS_TA_SET_API_KEY_ENABLED.name],
    )

# user_id may be username or id
@blueprint.route("/user/<user_id>/delete", methods=['POST'])
@login_required
@admin_only
def delete_user(user_id):
    if str(user_id).isdigit():
        user = User.get_by_id(int(user_id))
    else:
        user = User.query.filter_by(username=user_id).first()
    if user is None:
        flash("No such user", "info")
        abort(404)
    form = SubmitWithConfirmAndAuthForm(request.form)
    if form.is_submitted() and form.validate():
        user.delete()
        flash(f"OK, deleted user {user.pretty_username}", "success")
        return redirect(url_for("admin.list_users"))
    else:
        _flash_errors(form)
    flash(f"Did not delete user {user.pretty_username}", "warning")
    return redirect(url_for("admin.edit_user", user_id=user.id))

# user_id may be username or id
@blueprint.route("/user/<user_id>/edit", methods=['GET','POST'])
@login_required
@admin_only
def edit_user(user_id):
   return manage_user(user_id=user_id)

@blueprint.route("/api-keys", methods=['GET','POST'], strict_slashes=False)
@login_required
@staff_only
def api_keys():
    users = sorted(
      User.query.all(), key=lambda user: (user.is_staff, user.username)
    )
    form = ApiKeyForm(request.form)
    if request.method == "POST":
        want_api_key_generated = None
        if form.submit_generate_keys.data:
            want_api_key_generated = True
        elif form.submit_clear_keys.data:
            want_api_key_generated = False
        if want_api_key_generated is None:
            flash("Did not change any API keys: error in form (missing submit action)", "danger")
        else:
            valid_usernames = [user.username for user in users]
            bad_usernames = []
            good_usernames = []
            for username in form.usernames.data:
                if username in valid_usernames:
                    good_usernames.append(username)
                else:
                    bad_usernames.append(username)
            if bad_usernames:
                flash(f"Error: unrecognised users:{', '.join(bad_usernames)}", "danger")
            if good_usernames:
                changed_usernames = []
                unchanged_usernames = []
                for username in good_usernames:
                    user = User.query.filter_by(username=username).first()
                    old_key = user.api_key
                    user.generate_api_key(want_api_key_generated)
                    if user.api_key == old_key:
                        unchanged_usernames.append(username)
                    else:
                        user.save()
                        changed_usernames.append(username)
                if unchanged_usernames:
                    flash(f"API key was the same as before so nothing changed for {_user_summary(unchanged_usernames)}.", "warning")
                if changed_usernames:
                    if want_api_key_generated:
                        flash(f"OK, generated new API key for {_user_summary(changed_usernames)}.", "success")
                    else:
                        flash(f"OK, cleared API key for {_user_summary(changed_usernames)}.", "success")
            else:
                flash(f"Did not change any API keys: no users selected", "warning")
    form.usernames.choices = [u.username for u in users]
    api_secret_ttl_pretty=get_pretty_approx_duration(
        current_app.config[ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name]
    )
    return render_template(
       "admin/api_key.html",
       api_secret_ttl_pretty=api_secret_ttl_pretty,
       api_task_name=current_app.config[ConfigSettingNames.TASK_NAME_FOR_API.name],
       form=form,
       is_api_secret_otp=current_app.config[ConfigSettingNames.IS_API_SECRET_ONE_TIME_PW.name],
       is_student_api_otp_allowed=current_app.config[ConfigSettingNames.IS_STUDENT_API_OTP_ALLOWED.name],
       users=users,
    )

@blueprint.route("/api-test", methods=["GET"], strict_slashes=False)
@login_required
@staff_only
def api_test():
    return render_template(
        "admin/api_test.html",
        form=GeneralSubmitForm(), # for generate/clear key
        random_qty_wheels=random.randint(1,100),
        user=current_user, # for generate/clear key
    )

@blueprint.route("/user/<user_id>/buggy")
def show_buggy(user_id):
    """ Using the show_buggy code from Buggy: it's common for non-admin too"""
    # note that show_buggy_by_user checks the admin status of the requestor
    if str(user_id).isdigit():
        user = User.query.filter_by(id=int(user_id)).first_or_404()
        username = user.username
    else:
        username = user_id
    return show_buggy_by_user(username=username)

@blueprint.route("/user/<user_id>/buggy/delete", methods=["POST"])
@login_required
@admin_only
def delete_buggy(user_id):
    # note that delete_buggy_by_user checks the admin status of the requestor
    if str(user_id).isdigit():
        user = User.query.filter_by(id=int(user_id)).first_or_404()
        username = user.username
    else:
        username = user_id
    return delete_buggy_by_user(username=username)


@blueprint.route("/download/buggies/csv/all")
@login_required
@staff_only
def download_buggies_all():
    return download_buggies(want_students_only=False)

@blueprint.route("/download/buggies/csv")
@login_required
@staff_only
def download_buggies(want_students_only=True):
    """Download buggies as CSV (only format supported at the moment)"""
    buggies_with_users = Buggy.get_all_buggies_with_users(want_students_only=want_students_only)
    si = io.StringIO()
    cw = csv.writer(si)
    col_names = [col.name for col in Buggy.__mapper__.columns]
    col_names.insert(1, 'username')
    cw.writerow(col_names)
    for (b, u) in buggies_with_users:
        cw.writerow(
            [
                u.username if col == 'username' else getattr(b, col)
                for col in col_names
            ]
        )
    filename = get_download_filename("buggies.csv", want_datestamp=True)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/buggies/all", strict_slashes=False)
@login_required
@staff_only
def list_buggies_all():
    return list_buggies(want_students_only=False)

@blueprint.route("/buggies", strict_slashes=False)
@login_required
@staff_only
def list_buggies(want_students_only=True):
    """Admin buggy list."""
    buggies_and_users=Buggy.get_all_buggies_with_users(want_students_only=want_students_only)
    flag_color_css_defs = get_flag_color_css_defs(
        [buggy for (buggy, _) in buggies_and_users]
    )
    return render_template(
        "admin/buggies.html",
        buggies=buggies_and_users,
        flag_color_css_defs=flag_color_css_defs,
        want_students_only=want_students_only
    )

@blueprint.route("/settings/<group_name>", methods=['GET','POST'])
@blueprint.route("/settings", methods=['GET','POST'], strict_slashes=False)
@login_required
@admin_only
def settings(group_name=None):
    """Admin settings check page."""
    form = SettingForm(request.form)
    settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
    social_settings = SocialSetting.get_socials_from_config(settings_as_dict, want_all=True)
    if request.method == "POST":
        # group_name = form['group'].data
        if form.is_submitted() and form.validate():
            _update_settings_in_db(form)
            # inefficient, but update to reflect changes
            settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
            social_settings = SocialSetting.get_socials_from_config(settings_as_dict, want_all=True)
        else:
            _flash_errors(form)
    html_descriptions = { 
        setting: markdown.markdown(ConfigSettings.DESCRIPTIONS[setting])
        for setting in ConfigSettings.DESCRIPTIONS
    }
    groups_by_setting = {}
    for group in ConfigSettings.GROUPS:
        # TODO: auth group needs to be promoted to a list (missing comma)
        if group == ConfigGroupNames.AUTH.name:
            groups_by_setting[ConfigSettingNames.AUTHORISATION_CODE.name] = group.lower()
        else:
            for setting in ConfigSettings.GROUPS[group]:
                groups_by_setting[setting] = group.lower()
    pretty_group_name_dict = { name:ConfigSettings.pretty_group_name(name) for name in ConfigSettings.GROUPS }
    return render_template(
        "admin/settings.html",
        docs_url=current_app.config[ConfigSettingNames._BUGGY_RACE_DOCS_URL.name],
        env_setting_overrides=current_app.config[ConfigSettings.ENV_SETTING_OVERRIDES_KEY],
        form=form,
        groups_by_setting=groups_by_setting,
        group_name=group_name,
        groups=ConfigSettings.GROUPS,
        html_descriptions=html_descriptions,
        is_tech_note_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
        pretty_default_settings=ConfigSettings.get_pretty_defaults(),
        pretty_group_name_dict=pretty_group_name_dict,
        SETTING_PREFIX=SETTING_PREFIX,
        settings=settings_as_dict,
        social_settings=social_settings,
        sorted_groupnames=[name for name in ConfigSettings.SETUP_GROUPS],
        type_of_settings=ConfigSettings.TYPES,
    )

@blueprint.route("/announcements/no-html", strict_slashes=False)
@login_required
@admin_only
def list_announcements_without_html():
    return list_announcements(is_html_enabled=False)

@blueprint.route("/announcements", strict_slashes=False)
@login_required
@admin_only
def list_announcements(is_html_enabled=True):
    # only using the form for the CSRF token at this point
    form = AnnouncementActionForm(request.form)
    announcements = sorted(
        Announcement.query.all(),
        key=lambda announcement: (announcement.type, announcement.text)
    )
    has_example_already = bool(
        [
            ann for ann in announcements
            if ann.text == Announcement.EXAMPLE_ANNOUNCEMENT
        ]
    )
    return render_template(
        "admin/announcements.html",
        announcements=announcements,
        example_form=None if has_example_already else GeneralSubmitForm(),
        form=form,
        is_html_enabled=is_html_enabled
    )

@blueprint.route("/announcements/<int:announcement_id>/no-html", methods=["GET"])
def edit_announcement_without_html(announcement_id):
    """ exists solely to allow suppression of HTML inside announcement 
        in the event of an announcement having broken the page layout """
    return edit_announcement(announcement_id)

@blueprint.route("/announcements/<int:announcement_id>", methods=["GET", "POST"])
@blueprint.route("/announcements/new", methods=["GET", "POST"])
@login_required
@admin_only
def edit_announcement(announcement_id=None):
    announcement = None
    is_visible = False
    is_html =  False
    if announcement_id:
        announcement = Announcement.query.filter_by(id=announcement_id).first()
        if announcement is None:
            flash(f"No such announcement", "danger")
            return redirect(url_for("admin.list_announcements"))
    form = AnnouncementForm(request.form, obj=announcement)
    delete_form = AnnouncementActionForm()
    if request.method == "GET":
        if announcement:
            is_html=announcement.is_html
            is_visible=announcement.is_visible
    if request.method == "POST":
        if current_user.is_live_demo_user:
            flash(
                f"You did nothing wrong, but we don't let demo admin "
                "users change announcements on the demo server (sorry)",
                "danger"
            )
            return redirect(url_for("admin.list_announcements"))
        if form.is_submitted() and form.validate():
            if announcement is not None:
                announcement.text = form.text.data
                announcement.type = form.type.data
                announcement.is_visible = form.is_visible.data
                announcement.is_html = form.is_html.data
                announcement.save()
                flash("OK, updated announcement", "success")
                refresh_global_announcements(current_app)
                return redirect(url_for("admin.list_announcements"))
            else:
                Announcement.create(
                    text=form.text.data,
                    type=form.type.data,
                    is_html=form.is_html.data,
                    is_visible=False, # don't allow immediate publication: see it first
                )
                flash(f"Announcement created (but not displayed yet)", "success")
                return redirect(url_for("admin.list_announcements"))
        else:
            flash("Did not create an announcement!", "danger")
            flash_errors(form)
    return render_template(
        "admin/announcement_edit.html", 
        form=form, 
        id=announcement_id,
        is_html=is_html,
        is_visible=is_visible,
        announcement=announcement,
        type_option_groups=Announcement.TYPE_OPTION_GROUPS,
        delete_form=delete_form,
    )

@blueprint.route("/announcements/<int:announcement_id>/publish", methods=["POST"])
@login_required
@admin_only
def publish_announcement(announcement_id):
    form = AnnouncementActionForm(request.form)
    want_to_display = None
    if form.submit_hide.data:
        want_to_display = False
    elif form.submit_display.data:
        want_to_display = True
    if want_to_display is None:
        flash("Error: couldn't decide to display or not", "danger")
    else:
        announcement = Announcement.query.filter_by(id=announcement_id).first()
        if announcement is None:
            flash("Error: coudldn't find announcement", "danger")
        else:
            announcement.is_visible = want_to_display
            announcement.save()
            if want_to_display:
                flash("OK, unhid an announcement and displayed it", "success")
            else:
                flash("OK, hid an announcement", "success")
            refresh_global_announcements(current_app)
    announcements=Announcement.query.all()
    return render_template(
        "admin/announcements.html",
        announcements=announcements,
        form=form
    )

@blueprint.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
@login_required
@admin_only
def delete_announcement(announcement_id=None):
    form = AnnouncementActionForm(request.form)
    if form.submit_delete.data:
        if current_user.is_live_demo_user:
            flash(
                f"You did nothing wrong, but we don't let demo admin "
                "users delete announcements on the demo server (sorry)",
                "danger"
            )
            return redirect(url_for("admin.list_announcements"))
        announcement = Announcement.query.filter_by(id=announcement_id).first()
        if announcement is None:
            flash("Error: coudldn't find announcement to delete", "danger")
        else:
            announcement.delete()
            flash("OK, deleted announcement", "success")
            refresh_global_announcements(current_app)
    else:
        flash("Error: incorrect button wiring, nothing deleted", "danger")
    return redirect(url_for("admin.list_announcements"))

@blueprint.route("/announcements/new/example", methods=["POST"])
@login_required
@admin_only
def add_example_announcement():
    form = GeneralSubmitForm(request.form)
    if form.is_submitted() and form.validate():
        if current_user.is_live_demo_user:
            flash(
                f"You did nothing wrong, but we don't let demo admin "
                "users create announcements on the demo server (sorry)",
                "danger"
            )
            return redirect(url_for("admin.list_announcements"))
        Announcement.create(
            type="special",
            text=Announcement.EXAMPLE_ANNOUNCEMENT,
            is_html=True,
            is_visible=False,
        )
        flash("OK, inserted an example announcement", "success")
    else:
        flash("Problem with example announcement submit", "warning")
    return redirect(url_for("admin.list_announcements"))

@blueprint.route("/tech-notes/publish", methods=["POST", "GET"])
@login_required
@admin_only
def tech_notes_publish():
    if request.method == "GET":
         # convenience for testing: publishing only makes sense with POST
        return redirect(url_for('admin.tech_notes_admin'))
    return tech_notes_admin()

@blueprint.route("/tech-notes", methods=["GET"], strict_slashes=False)
@login_required
@admin_only
def tech_notes_admin():
  error_msg = None
  form = GeneralSubmitForm(request.form) # no auth required
  if request.method == "POST":
      if form.is_submitted() and form.validate():
          try:
              output_msg = publish_tech_notes(current_app)
          except Exception as e:
              error_msg = f"Error: {e}"
              flash(error_msg, "danger")
          else:
              flash(output_msg, "info")
              flash("Re-generated tech notes (static web pages) OK", "success")
              if _is_from_dashboard():
                  return redirect(url_for('admin.admin'))
      else:
          flash_errors(form)
  return render_template(
    "admin/tech_notes.html",
    form=FlaskForm(request.form), # nothing except CSRF token
    is_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
    key_settings=[
        ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name,
        ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
        ConfigSettingNames.PROJECT_CODE.name,
        ConfigSettingNames.SOCIAL_0_NAME.name,
        ConfigSettingNames.SOCIAL_1_NAME.name,
        ConfigSettingNames.SOCIAL_2_NAME.name,
        ConfigSettingNames.SOCIAL_3_NAME.name,
    ],
    notes_generated_timestamp=servertime_str(
        current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
        current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name]
    ),
    tech_notes_external_url=current_app.config[ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name],
  )

@blueprint.route("/tasks/publish", methods=["POST"])
@login_required
@admin_only
def tasks_generate():
    form = GeneralSubmitForm(request.form) # no auth required
    if form.is_submitted() and form.validate():
        # render the template and save it as _task_list.html
        try:
            publish_task_list(current_app)
            publish_tasks_as_issues_csv(current_app)
        except IOError as e:
            flash(f"Failed to create task list: problem with file: {e}", "danger")
        else:
            qty_tasks = Task.query.filter_by(is_enabled=True).count()
            if qty_tasks == 0:
                flash("Task list page has been generated but there are no unhidden tasks in the project yet!", "danger")
                flash("You should load some tasks into the database before the project can start", "warning")
            else:
                flash(f"OK, task list page has been generated with latest data ({qty_tasks} tasks)", "success")
            if _is_from_dashboard():
                return redirect(url_for('admin.admin'))
    return redirect(url_for('admin.tasks_admin'))

@blueprint.route("/tasks/all", methods=["GET"], strict_slashes=False)
@login_required
@admin_only
def tasks_admin_all():
    return tasks_admin()

@blueprint.route("/tasks/load", methods=["GET", "POST"], strict_slashes=False)
@login_required
@admin_only
def tasks_load():
    form = GenerateTasksForm(request.form)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if want_overwrite := form.is_confirmed.data:
                md_filename_with_path = join_to_project_root(
                    current_app.config[ConfigSettingNames._PROJECT_TASKS_DIR_NAME.name],
                    current_app.config[ConfigSettingNames._PROJECT_TASKS_FILENAME.name]
                )
                delete_path = None
                pretty_source = "default tasks"
                is_success = False
                if "markdown_file" in request.files and request.files['markdown_file']:
                    md_file = request.files['markdown_file']
                    if md_file.filename:
                        md_filename_with_path = os.path.join(
                            current_app.config['UPLOAD_FOLDER'],
                            secure_filename(md_file.filename)
                        )
                        md_file.save(md_filename_with_path)
                        delete_path = md_filename_with_path
                        pretty_source = "uploaded tasks"
                    else:
                        flash(f"Uploaded file seems empty", "danger")
                        abort(500)
                else:
                    # using default tasks (because no file was uploaded)
                    try:
                        distrib_method = DistribMethods(form.distrib_method.data)
                    except ValueError: # unrecognised method name from form
                        distrib_method = None

                    # this creates a combo file from defaults _as if it has been uploaded_
                    md_filename_with_path=create_default_task_markdown_file(
                        distrib_method.value if distrib_method else None
                    )
                    if distrib_method:
                        pretty_source += f" (with distribution method: \"{distrib_method.desc}\")"
                    delete_path = md_filename_with_path
                try:
                    qty_tasks_added = load_tasks_into_db(
                        join_to_project_root(md_filename_with_path),
                        app=current_app,
                        want_overwrite=want_overwrite,
                    )
                    flash(
                        f"OK, put {qty_tasks_added} {pretty_source} into the database",
                        "success"
                    )
                    flash(
                        "Remember to publish the task list now! "
                        "...unless you're going to edit any tasks first",
                        "info"
                    )
                    is_success = True
                except Exception as e:
                    flash(f"Error parsing/adding tasks: {e}", "danger")
                if delete_path:
                    try:
                        os.unlink(delete_path)
                    except os.error as e:
                        # could sanitise this, but the diagnostic might be useful
                        flash(f"Problem deleting uploaded file: {e}", "warning")
                if is_success:
                    return redirect(url_for('admin.tasks_admin'))
            else:
                flash(f"Did not not load tasks because you did not explicity confirm it", "danger")
        else:
            flash_errors(form)
    qty_texts = TaskText.query.count()
    text_authors = [] if qty_texts == 0 else TaskText.get_all_task_text_authors()
    return render_template(
        "admin/tasks_load.html",
        qty_texts=qty_texts,
        text_authors=text_authors,
        qty_tasks=Task.query.count(),
        auto_republish_config_name=ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name,
        distrib_methods=DistribMethods,
        form=form,
        key_settings=[
          ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
          ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name,
          ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name,
        ],
        task_list_updated_timestamp=current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
        tasks_loaded_at=current_app.config[ConfigSettingNames._TASKS_LOADED_DATETIME.name],
    )

@blueprint.route("/tasks", methods=["GET"], strict_slashes=False)
@login_required
@admin_only
def tasks_admin():
    form = GeneralSubmitForm(request.form) # just for csrf on publish button
    tasks_loaded_at = current_app.config[ConfigSettingNames._TASKS_LOADED_DATETIME.name]
    tasks_published_at = current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name]
    is_fresh_update = tasks_loaded_at and tasks_published_at and \
                      (tasks_published_at < tasks_loaded_at)
    want_all = request.path.endswith("all")
    tasks = Task.query.order_by(
        Task.phase.asc(),
        Task.sort_position.asc()
    ).all()
    qty_disabled_tasks = len([task for task in tasks if not task.is_enabled])
    if not want_all:
        tasks = [task for task in tasks if task.is_enabled]
    qty_tasks = len(tasks)
    if qty_tasks:
        example_task = tasks[int(qty_tasks/2)]
        example_task_url = example_task.get_url(current_app.config)
    else:
        example_task = None
        example_task_url = None
    is_injecting_github_issues = (
        current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_FORK.name]
        and
        current_app.config[ConfigSettingNames.IS_USING_GITHUB_API_TO_INJECT_ISSUES.name]
    )
    return render_template(
        "admin/tasks.html",
        auto_republish_config_name=ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name,
        distrib_methods=DistribMethods,
        example_task_url=example_task_url,
        example_task=example_task,
        is_fresh_update=is_fresh_update,
        is_injecting_github_issues=is_injecting_github_issues,
        is_showing_all_tasks=want_all,
        key_settings=[
          ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
          ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name,
          ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name,
        ],
        qty_disabled_tasks=qty_disabled_tasks,
        qty_tasks=qty_tasks,
        task_list_updated_timestamp=current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
        tasks_loaded_at=current_app.config[ConfigSettingNames._TASKS_LOADED_DATETIME.name],
        tasks=tasks,
        form=form,
    )

@blueprint.route("/download/tasks/<type>/<format>", methods=["GET", "POST"])
@login_required
@admin_only
def download_tasks(type=None, format=None):
    CURRENT = "current"
    DEFAULT = "default"
    FORMAT_MARKDOWN = "md"
    FORMAT_CSV = "csv"
    DOWNLOAD_TYPES = [DEFAULT, CURRENT]
    DOWNLOAD_FORMATS = [FORMAT_MARKDOWN, FORMAT_CSV]
    if type not in DOWNLOAD_TYPES:
        flash(f"Unknown task type \"{type}\": should be one of {' or '.join(DOWNLOAD_TYPES)}", "danger")
        abort(404)
    if format not in DOWNLOAD_FORMATS:
        flash(f"Unknown task format \"{format}\": should be one of {' or '.join(DOWNLOAD_FORMATS)}", "danger")
        abort(404)
    if type == DEFAULT:
        if format == FORMAT_CSV:
            flash(f"Cannot download default issues in CSV format", "danger")
            abort(404)
        default_task_md_file=create_default_task_markdown_file(
            DistribMethods.get_default_value()
        )
        infile = open(default_task_md_file)
        payload = "".join(infile.readlines())
        infile.close()
        try:
            os.unlink(default_task_md_file)
        except os.error as e:
            pass # failure to delete is untidy but not important
        filename = get_download_filename(f"tasks-{type}.{format}", want_datestamp=False)
    elif type == CURRENT:
        tasks = Task.query.filter_by(is_enabled=True).order_by(
            Task.phase.asc(),
            Task.sort_position.asc()
        ).all()
        if format == FORMAT_CSV:
            payload = get_tasks_as_issues_csv(
                tasks,
                current_app.config[ConfigSettingNames.BUGGY_EDITOR_ISSUES_CSV_HEADER_ROW.name],
                is_line_terminator_crlf=current_app.config[ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name]
            )
        else:
            payload = "".join([task.raw_markdown for task in tasks if task.is_enabled])
        filename = get_download_filename(f"tasks-{type}.{format}", want_datestamp=True)
    return Response(
        payload,
        headers={"Content-disposition": f"attachment; filename=\"{filename}\""},
        mimetype="text/plain",
    )

@blueprint.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def edit_task(task_id=None):
    task = None
    if str(task_id).isdigit():
        task = Task.get_by_id(int(task_id))
    else:
        (phase, name) = Task.split_fullname(task_id)
        if phase is not None:
            task = Task.query.filter_by(phase=phase, name=name).first()
    if task is None:
        abort(404)
      # Note: not allowing addition of new tasks here.
      # This is a policy decision not a technical one.
      # You can add entirely new tasks by uploading the
      # markdown file, but after that: only tweaks and/or
      # en/disabling them (effectively deleting them).
    form = TaskForm(request.form, obj=task)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            task.phase = form.phase.data
            task.name = form.name.data
            task.title = form.title.data
            task.problem_text = form.problem_text.data
            task.solution_text = form.solution_text.data
            task.hints_text = form.hints_text.data
            task.sort_position = form.sort_position.data
            changed_is_enabled = task.is_enabled != form.is_enabled.data
            task.is_enabled = form.is_enabled.data
            task.save()
            flash(f"OK, updated task { task.fullname }", "success")
            if changed_is_enabled:
                if task.is_enabled:
                  msg = f"When you undelete a task like this, it doesn't appear in the project until you regenerate the task list"
                else:
                  msg = f"When you delete a task like this, it won't disappear from the project until you regenerate the task list"
                flash(msg, "info")
            set_and_save_config_setting(
                current_app,
                ConfigSettingNames._TASKS_EDITED_DATETIME.name,
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            )
            return redirect(url_for('admin.tasks_admin'))
        else:
            flash_errors(form)
    return render_template(
      "admin/task_edit.html",
      form=form,
      task=task,
    )

@blueprint.route("/json/latest-json/<user_id>", methods=["GET"])
def get_uploaded_json_for_user(user_id):
  payload = ""
  if current_user and current_user.is_authenticated and current_user.is_staff:
    user = User.get_by_id(user_id)
    if user is None:
      status = 404
    else:
      status = 200
      payload = {       
          "user_id": user_id,
          "text": user.latest_json,
          "uploaded_at": stringify_datetime(user.uploaded_at),
        }
  else:
      status = 403
  response = make_response(jsonify(payload), status)
  response.headers["Content-type"] = "application/json"
  return response

@blueprint.route("/json/text/<text_id>", methods=["GET"])
def get_text_for_user_task(text_id):
  payload = ""
  if current_user and current_user.is_authenticated and current_user.is_staff:
      text = TaskText.get_by_id(text_id)
      if text is None:
          status = 404
      else:
          status = 200
          payload = {
              "id": text.id,
              "created_at": stringify_datetime(text.created_at),
              "modified_at": stringify_datetime(text.modified_at),
              "user_id": text.user_id,
              "task_id": text.task_id,
              "text": text.text,
            }
  else:
      status = 403
  response = make_response(jsonify(payload), status)
  response.headers["Content-type"] = "application/json"
  return response

@blueprint.route("/task-texts-matrix", methods=["GET"], strict_slashes=False)
@login_required
@staff_only
def task_texts():
    # TODO: this should be using joins and stuff but let's make python
    #       do the work for now and optimise/make it robust when we know
    #       from playing with the page what we really need here...
    #       Possibly all in JSON too for interactive graphing on the page
    tasks = Task.query.filter_by(is_enabled=True).order_by(Task.phase.asc(), Task.sort_position.asc()).all()
    if not tasks:
        flash("Cannot display texts because there are no tasks — maybe you need to load them into the database?", "warning")
        return redirect(url_for("admin.admin"))
    students = User.query.filter_by(is_active=True, is_student=True).order_by(User.username.asc()).all()
    usernames_by_id = {student.id: student.username for student in students}
    texts_by_username = {student.username: {} for student in students}
    for text in TaskText.query.all():
        if text.user_id in usernames_by_id: # TODO in lieu of a JOIN on active students
            texts_by_username[usernames_by_id[text.user_id]][text.task_id] = text
    buggies_by_username = {student.username: {} for student in students}
    for buggy in Buggy.query.all():
        if buggy.user_id in usernames_by_id: # TODO in lieu of a JOIN on active students
           buggies_by_username[usernames_by_id[buggy.user_id]] = buggy
    return render_template(
       "admin/task_texts_matrix.html",
       buggies_by_username=buggies_by_username,
       students=students,
       tasks=tasks,
       texts_by_username=texts_by_username,
    )

@blueprint.route("/task-texts", methods=["GET"], strict_slashes=False)
@login_required
@staff_only
def task_texts_details():
    tasks = Task.query.filter_by(is_enabled=True).order_by(Task.phase.asc(), Task.sort_position.asc()).all()
    if not tasks:
        flash("Cannot display texts because there are no tasks — maybe you need to load them into the database?", "warning")
        return redirect(url_for("admin.admin"))
    students = User.query.filter_by(is_active=True, is_student=True).order_by(User.username.asc()).all()
    pretty_usernames_by_id = {student.id: student.pretty_username for student in students}
    texts_by_task_id=TaskText.get_dict_texts_by_task_id(None) # no specific user
    tasks_by_phase=Task.get_dict_tasks_by_phase(want_hidden=False)
    nonauthors_by_task_id = defaultdict(list)
    for phase in tasks_by_phase:
        for task in tasks_by_phase[phase]:
            texts_by_task_id[task.id] = sorted(
                texts_by_task_id.get(task.id) or [],
                key=lambda text: pretty_usernames_by_id.get(text.user_id)
            )
            author_ids = [ text.user_id for text in texts_by_task_id[task.id] ]
            nonauthors_by_task_id[task.id] = [
                student.id for student in students
                if student.id not in author_ids
            ]
    return render_template(
      "admin/task_texts_details.html",
      nonauthors_by_task_id=nonauthors_by_task_id,
      pretty_usernames_by_id=pretty_usernames_by_id,
      qty_students=len(students),
      students=students,
      tasks_by_phase=Task.get_dict_tasks_by_phase(want_hidden=False),
      texts_by_task_id=texts_by_task_id,
    )



@blueprint.route("/settings/<setting_name>/delete", methods=["POST"])
@login_required
@staff_only
def purge_unexpected_config_setting(setting_name):
    """ Purge a config setting that has been reported as unexpected:
    In practice this is a housekeeping activity for development: unexpected
    settings are typically legacy config settings that remain in the database
    after being removed from the code.
    """
    unexpected_settings =  current_app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY]
    if setting_name not in unexpected_settings:
       flash(f"Cannot purge config setting \"{setting_name}\": it's not reported as unexpected", "warning")
       return redirect(url_for("admin.admin"))
    actual_name = "" if setting_name == ConfigSettings.NO_KEY else setting_name
    dead_setting = Setting.query.filter_by(id=actual_name).first()
    if dead_setting is None:
       flash(f"Cannot purge config setting \"{actual_name}\": can't find it", "danger")
       return redirect(url_for("admin.admin"))
    dead_setting.delete()
    current_app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY] = [
       name for name in unexpected_settings if name != setting_name
    ]
    flash(f"OK, purged config setting \"{setting_name}\"", "success")
    return redirect(url_for("admin.admin"))

@blueprint.route("/system", strict_slashes=False, methods=["GET"])
@login_required
@admin_only
def show_system_info():
    # mysql+mysqlconnector://beholder:XXXXX@localhost:8889/buggydev
    db_url = current_app.config.get("DATABASE_URL")
    redacted_db_url = redact_password_in_database_url(db_url)
    alchemy_db_url = current_app.config.get(ConfigSettings.SQLALCHEMY_DATABASE_URI_KEY)
    redacted_alchemy_db_url = redact_password_in_database_url(alchemy_db_url)
    try:
        result = subprocess.run(
          "git rev-parse --short HEAD; git branch --show-current",
          shell=True, text=True, capture_output=True, check=True
        )
        git_status = result.stdout
    except (ValueError, subprocess.CalledProcessError) as e:
        git_status = "[Unavailable]"
    announcement_summary = None
    if curr_anns := current_app.config.get(ConfigSettingNames._CURRENT_ANNOUNCEMENTS.name):
        try:
            qty_anns = curr_anns.count()
            if qty_anns == 1:
                announcement_summary = "1 announcement"
            elif qty_anns > 1:
                announcement_summary = f"{qty_anns} announcements"
        except AttributeError as e:
            announcement_summary = f"(unexpected type): {curr_anns}"
    return render_template(
        "admin/system_info.html",
        config_settings_to_display=sorted(ConfigSettings.get_extra_names_for_config_dump()),
        env_overrides_key=ConfigSettings.ENV_SETTING_OVERRIDES_KEY,
        env_overrides=current_app.config[ConfigSettings.ENV_SETTING_OVERRIDES_KEY],
        git_status=git_status,
        forced_db_uri_ssl_mode_key=ConfigSettings.FORCED_DB_URI_SSL_MODE_KEY,
        forced_db_uri_ssl_mode=current_app.config[ConfigSettings.FORCED_DB_URI_SSL_MODE_KEY],
        is_db_uri_password_as_query_key=ConfigSettings.REWRITING_DB_URI_PASSWORD_KEY,
        is_db_uri_password_as_query=current_app.config[ConfigSettings.REWRITING_DB_URI_PASSWORD_KEY],
        redacted_database_url=redacted_db_url,
        redacted_alchemy_database_url=redacted_alchemy_db_url,
        unexpected_config_settings=current_app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY],
        version_from_source=current_app.config[ConfigSettingNames._VERSION_IN_SOURCE.name],
        announcement_summary=announcement_summary,
    )


@blueprint.route("/buggy-editor", strict_slashes=False, methods=["GET"])
@login_required
@admin_only
def show_buggy_editor_info():
    return render_template(
      "admin/buggy_editor.html",
      **_get_buggy_editor_kwargs(current_app),
      is_editor_zipfile_published=_is_editor_zipfile_published(),
      editor_zip_generated_datetime=current_app.config[ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name],
      readme_filename=current_app.config[ConfigSettingNames._EDITOR_README_FILENAME.name],
      delete_form=SubmitWithConfirmForm()
   )

@blueprint.route("/buggy-editor/delete", strict_slashes=False, methods=["POST"])
@login_required
@admin_only
def delete_buggy_editor_zip():
    form = SubmitWithConfirmForm(request.form)
    if form.is_submitted() and form.validate():
        if current_user.is_live_demo_user:
            flash(
                f"You did nothing wrong, but we don't let demo admin "
                "users delete the buggy editor zipfile on the demo server (sorry)",
                "danger"
            )
            return redirect(url_for("admin.show_buggy_editor_info"))
        if form.is_confirmed.data:
            zipfilename = current_app.config[ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name]
            target_zipfile = join_to_project_root(
                current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
                current_app.config[ConfigSettingNames._EDITOR_OUTPUT_DIR.name],
                zipfilename
            )
            try:
                os.unlink(target_zipfile)
            except os.error as e:
                flash(f"Problem deleting \"{zipfilename}\": {e}", "danger")
            else:
                flash(f"OK, deleted \"{zipfilename}\"", "success")
        else:
            flash("Did not delete zipfile because you did not explicitly confirm it", "danger")
    else:
        flash("Wiring error, can't delete", "danger")
    return redirect(url_for("admin.show_buggy_editor_info"))

@blueprint.route("/buggy-editor/publish", methods=['GET', 'POST'])
@login_required
@admin_only
def publish_editor_zip():
    readme_filename = current_app.config[ConfigSettingNames._EDITOR_README_FILENAME.name]
    editor_python_filename = current_app.config[ConfigSettingNames._EDITOR_PYTHON_FILENAME.name]
    is_writing_server_url_in_editor = current_app.config[ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name]
    is_writing_host_and_port_in_editor = current_app.config[ConfigSettingNames.IS_WRITING_HOST_AND_PORT_IN_EDITOR.name]
    form = PublishEditorSourceForm(request.form)
    if request.method == "POST":
        readme_contents = form.readme_contents.data
        is_writing_server_url_in_editor = form.is_writing_server_url_in_editor.data
        # save setting as config (so autogeneration can reproduce it)
        # this is also about to be used by the create_editor_zipfile()
        set_and_save_config_setting(
            current_app,
            name=ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name,
            value=1 if is_writing_server_url_in_editor else 0
        )
        current_app.config[ConfigSettingNames.IS_WRITING_SERVER_URL_IN_EDITOR.name] = is_writing_server_url_in_editor

        is_writing_host_and_port_in_editor = form.is_writing_host_and_port_in_editor.data
        set_and_save_config_setting(
            current_app,
            name=ConfigSettingNames.IS_WRITING_HOST_AND_PORT_IN_EDITOR.name,
            value=1 if is_writing_host_and_port_in_editor else 0
        )
        current_app.config[ConfigSettingNames.IS_WRITING_HOST_AND_PORT_IN_EDITOR.name] = is_writing_host_and_port_in_editor

        try:
            create_editor_zipfile(readme_contents, app=current_app)
        except (FileNotFoundError, IOError) as e:
            flash("Failed to save zip file: {e}", "danger")
            return redirect(url_for("admin.show_buggy_editor_info"))

        # save this README in database so auto-generation can reproduce it
        readme_db_file = DbFile.query.filter_by(
            type=DbFile.README_TYPE
        ).first() # don't care about item_id: there is only ever one
        if readme_db_file is None:
            readme_db_file = DbFile.create(type=DbFile.README_TYPE)
        readme_db_file.contents = readme_contents
        readme_db_file.save()
        set_and_save_config_setting(
            current_app,
            name=ConfigSettingNames._EDITOR_ZIP_GENERATED_DATETIME.name,
            value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        )

        if is_writing_server_url_in_editor:
            server_url = current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
            flash(
                f"Hardcoded BUGGY_RACE_SERVER_URL=\"{server_url}\" within {editor_python_filename}",
                "info"
            )
        if is_writing_host_and_port_in_editor:
            host = current_app.config[ConfigSettingNames.EDITOR_HOST.name]
            port = current_app.config[ConfigSettingNames.EDITOR_PORT.name]
            flash(
                f"Hardcoded default host and port to \"{host}:{port}\" within {editor_python_filename}",
                "info"
            )
        qty_lines_in_readme = readme_contents.count("\n")
        flash(
            f"Wrote {qty_lines_in_readme} lines into {readme_filename}",
            "info"
        )
        flash("OK, editor files now zipped up and published", "success")
        flash("You should download the zip file, unzip it and check its contents before you distribute it to students!", "info")
        return redirect(url_for("admin.show_buggy_editor_info"))
    else:
        readme_contents = render_template(
            "admin/_buggy_editor_readme.txt",
            **_get_buggy_editor_kwargs(current_app),
        )
        form.readme_contents.data = readme_contents
        qty_lines_in_readme=readme_contents.count("\n") + 1
    return render_template(
        "admin/buggy_editor_publish.html",
        form=form,
        is_writing_server_url_in_editor=is_writing_server_url_in_editor,
        is_writing_host_and_port_in_editor=is_writing_host_and_port_in_editor,
        qty_lines_in_readme=qty_lines_in_readme,
        readme_filename=readme_filename,
        editor_source_commit=current_app.config[ConfigSettingNames._BUGGY_EDITOR_SOURCE_COMMIT.name],
        buggy_editor_origin_github_url=current_app.config[ConfigSettingNames._BUGGY_EDITOR_ORIGIN_GITHUB_URL.name],
        editor_python_filename=editor_python_filename,
    )

@blueprint.route("/buggy-editor/download", strict_slashes=False)
@login_required
@staff_only
def download_editor_zip_for_admin():
    """ Special case to allow admin to download published editor zipfile even
    if settings prevent students having access: this sends if the file exists,
    regardless of settings, potentially useful for _making_ the zip to then
    distribute elsewhere."""
    zipfile = join_to_project_root(
        current_app.config[ConfigSettingNames._PUBLISHED_PATH.name],
        current_app.config[ConfigSettingNames._EDITOR_OUTPUT_DIR.name],
        current_app.config[ConfigSettingNames.BUGGY_EDITOR_ZIPFILE_NAME.name]
    )
    if not os.path.exists(zipfile):
        flash("Editor zip file not available (has not been published)", "danger")
        abort(404)
    return send_file(zipfile)


@blueprint.route("/pre-reg-csv-utility", strict_slashes=False, methods=["GET", "POST"])
@login_required
@admin_only
def pre_registration_csv_utility():
    """ generating a CSV that only contains necessary columns for registration"""
    form = SimpleStringForm(request.form)
    if request.method == "POST":
        # this is just a boomerang upload-to-download call: sending the CSV data
        # that was generated by the javascript in the browser, so we can use the
        # server-side ability to set set Content-disposition headers (!)
        if form.is_submitted() and form.validate():
            csv_data = form.data.data
            filename = get_download_filename("students.csv", want_datestamp=True)
            output = make_response(csv_data)
            output.headers["Content-Disposition"] = f"attachment; filename={filename}"
            output.headers["Content-type"] = "text/csv"
            return output
        else:
            flash_errors(form)
    csv_fieldnames = ['username', 'password'] + ConfigSettings.users_additional_fieldnames(current_app)
    return render_template(
        "admin/pre_reg_csv_utility.html",
        csv_fieldnames=csv_fieldnames,
        ext_id_name=current_app.config[ConfigSettingNames.EXT_ID_NAME.name],
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        form=form,
        users_have_email=current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name],
        users_have_ext_id=current_app.config[ConfigSettingNames.USERS_HAVE_EXT_ID.name],
        users_have_ext_username=current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name],
        users_have_first_name=current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name],
        users_have_last_name=current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name],
    )

@blueprint.route("race/replay/stripped-down")
@login_required
@staff_only
def stripped_down_race_replayer():
    return render_template(
        "races/player_stripped_down.html",
        cachebuster=current_app.config[ConfigSettings.CACHEBUSTER_KEY],
        current_user_username="nobody!", # ensure no username match with "!"
        race_file_url="{{}}", # force JavaScript into believing it's standalone
    )

@blueprint.route("race/replay")
@login_required
@staff_only
def staff_race_replayer():
    """ race replayer for staff testing that isn't linked to datatabase races:
    this will try to load whatever URL is passed into the ?race= query var.
    This isn't suitable for replaying races for students because only staff can
     access it — but can be handy for testing new race files."""
    return render_template(
        "races/player.html",
        cachebuster=current_app.config[ConfigSettings.CACHEBUSTER_KEY],
        current_user_username=current_user.username,
        race_file_url="{{}}" # force JavaScript into believing it's standalone
    )

@blueprint.route("/config-docs-helper")
@login_required
@admin_only
def config_docs_helper():
    """ undocumented helper method for dumping config setting markdown for www site"""
    if not current_app.config[ConfigSettingNames._IS_DOCS_HELPER_PAGE_ENABLED.name]:
        flash("To see the documentation helper page, set config _IS_DOCS_HELPER_PAGE_ENABLED=1", "warning")
        abort(404)
    pretty_group_name_dict = { name:ConfigSettings.pretty_group_name(name) for name in ConfigSettings.GROUPS }
    pretty_default_settings=ConfigSettings.get_pretty_defaults()
    return render_template(
        "admin/config_docs_helper.html",
        descriptions={
            name: re.sub(r"(\n|\s)+", " ", ConfigSettings.DESCRIPTIONS[name])
            for name in ConfigSettings.DESCRIPTIONS
        },
        groups=ConfigSettings.GROUPS,
        md_pretty_default_settings={
            name: "_none/empty_" if pretty_default_settings[name] == "" else f"`{pretty_default_settings[name]}`"
            for name in pretty_default_settings
        },
        pretty_group_name_dict=pretty_group_name_dict,
        sorted_groupnames=[name for name in ConfigSettings.SETUP_GROUPS],
    )

@blueprint.route("/config/dump")
@login_required
@admin_only
def config_dump_as_dotenv():
    config_keys = sorted([
        k for k in
        list(
            set(
                ConfigSettings.get_extra_names_for_config_dump()
                +
                list(ConfigSettings.DEFAULTS.keys())
            )
        )
    ])
    # not useful when loading a new buggy racing server:
    EXCLUDE_FROM_DUMP = [
        'FLASK_DEBUG', 
        '_ANNOUNCEMENT_TOP_OF_PAGE_TYPES'
    ]
    config_text_lines = [
        "# config dump (suitable as .env?) of buggy race server "
        f"{current_app.config.get(ConfigSettingNames.BUGGY_RACE_SERVER_URL.name)}",
        ""
    ]
    for config_key in config_keys:
        if current_app.config.get(config_key) is not None:
            value = current_app.config.get(config_key)
            if config_key in EXCLUDE_FROM_DUMP:
                continue # explicitly skip unwanted entries
            if config_key in ConfigSettings.TYPES:
                type = ConfigSettings.TYPES[config_key]
                if type in [ConfigTypes.PASSWORD, ConfigTypes.SENSITIVE_STRING]:
                    continue # don't include passwords, etc
                if type == ConfigTypes.BOOLEAN:
                    value = 1 if current_app.config.get(config_key) else 0
            elif config_key.startswith("IS_"): # clunky boolean catcher
                value = 1 if current_app.config.get(config_key) else 0
            config_text_lines.append(
                f"{config_key}={value}"
            )
    filename = get_download_filename("buggy-dotenv.txt", want_datestamp=True) 
    return Response(
        "\n".join(config_text_lines),
        headers={"Content-disposition": f"attachment; filename=\"{filename}\""},
        mimetype="text/plain",
    )


@blueprint.route("/routes")
@login_required
@admin_only
def get_blueprint_urls():
    """ undocumented helper method for dumping all the Blueprint URLs """
    routes = [str(p) for p in current_app.url_map.iter_rules()]
    title = f"Blueprint routes ({len(routes)})"
    return render_template(
        "admin/system.html",
        system_str="\n".join(sorted(routes)),
        title=title,
    )

@blueprint.route("/user/<user_id>/texts-admin", methods=['GET', 'POST'])
@login_required
@admin_only
def user_upload_texts(user_id):
    if not current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
        flash("Task texts are not enabled on this project", "warning")
        abort(404)
    if str(user_id).isdigit():
        user = User.get_by_id(int(user_id))
    else:
        user = User.query.filter_by(username=user_id).first()
    if user is None:
        abort(404)
    form = UploadTaskTextsForm(request.form)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if form.is_confirmed.data:
                is_ignoring_warnings = form.is_ignoring_warnings.data
                if "texts_json_file" in request.files:
                    is_ok = False
                    json_file = request.files['texts_json_file']
                    if json_file.filename:
                        json_filename_with_path = os.path.join(
                            current_app.config['UPLOAD_FOLDER'],
                            f"texts-user-{user.username}.json"
                        )
                        json_file.save(json_filename_with_path)
                        try:
                            with open(json_filename_with_path, "r") as read_file:
                                result_data = json.load(read_file)
                            is_ok = True
                        except UnicodeDecodeError as e:
                            flash(
                                "Encoding error (maybe that wasn't a JSON file you uploaded, "
                                "or it contains unexpected characters?)",
                                "warning"
                            )
                        except json.decoder.JSONDecodeError as e:
                            flash("Failed to parse JSON data", "danger")
                            flash(str(e), "warning")
                            flash("No data was accepted", "info")
                        if is_ok:
                            has_warnings = False
                            tasks = Task.query.all()
                            tasks_by_full_name = {task.fullname: task for task in tasks}
                            qty_texts_by_task = defaultdict(int)
                            qty_tasks_with_bad_name = 0
                            task_with_mismatch_username = []
                            task_with_mismatch_task_name = []
                            bad_usernames = []
                            for text in result_data:
                                task_name = text.get('task_name')
                                if task_name is None:
                                    qty_tasks_with_bad_name += 1
                                    continue
                                qty_texts_by_task[task_name] += 1
                                if tasks_by_full_name.get(task_name) is None:
                                    task_with_mismatch_task_name.append(task_name)
                                username = text.get('username')
                                if username != user.username:
                                    task_with_mismatch_username.append(task_name)
                                    if username not in bad_usernames:
                                        bad_usernames.append(username)
                            task_with_mismatch_username.sort()
                            task_with_mismatch_task_name.sort()
                            flash(f"Number of texts found in uploaded JSON file: {len(result_data)}", "info")                            
                            if qty_tasks_with_bad_name > 0:
                                flash(f"Warning: some texts refered to tasks without names: {qty_tasks_with_bad_name}", "danger")
                                has_warnings = True
                            if task_with_mismatch_task_name:
                                flash(f"Warning: some texts refered to tasks that cannot be found: {', '.join(task_with_mismatch_task_name)}", "danger")
                                has_warnings = True
                            if task_with_mismatch_username:
                                flash(f"Warning: you're loading texts for user \"{user.pretty_username}\", but that's not the author of these texts: {', '.join(task_with_mismatch_username)}", "danger")
                                if len(bad_usernames) == 1:
                                    flash(f"Warning: the 'original' username in the texts you uploaded is \"{ bad_usernames[0] }\"", "danger")
                                else:
                                    flash(f"Warning: the 'original' usernames in the texts you uploaded are: {', '.join(map(quote_string, sorted(bad_usernames)))}", "danger")
                                has_warnings = True
                            if has_warnings and not is_ignoring_warnings:
                                flash("No changes were made (because you chose not to ignore warnings)", "info")
                            else:
                                if has_warnings and is_ignoring_warnings:
                                    flash("Making changes because you opted to ignore warnings", "warning")
                                qty_texts_deleted = TaskText.query.filter_by(user_id=user.id).delete()
                                db.session.commit() # force the deletion!
                                if qty_texts_deleted == 1:
                                    flash(f"Deleted one task text for user {user.pretty_username}", "info")
                                else:
                                    flash(f"Deleted {qty_texts_deleted} task texts for user {user.pretty_username}", "info")
                                qty_new_texts = 0
                                uploaded_at = datetime.now(timezone.utc)
                                for text in result_data:
                                    task_name = text.get('task_name')
                                    task = tasks_by_full_name.get(task_name)
                                    if task is None:
                                        flash(f"Failed to add text: no such task \"{ task_name }\"", "danger")
                                    else:
                                        created_at = uploaded_at
                                        try: # for now, assume no seconds (see utils.get_user_task_texts_as_list)
                                            created_at=datetime.strptime(text.get("created_at"), "%Y-%m-%d %H:%M")
                                        except TypeError:
                                            pass
                                            # failure to parse created_at isn't critical:
                                            # so fail silently, fallback to 'now'
                                        text_body = text.get("text")
                                        tasktext = TaskText(
                                            user_id=user.id,
                                            task_id=task.id,
                                            text=text_body,
                                            created_at=created_at,
                                            modified_at=uploaded_at,
                                        )
                                        tasktext.save()
                                        qty_new_texts += 1
                                        flash(f"Added task text for {task.fullname} by user {user.pretty_username} ({len(text_body)} characters)", "info")
                                if qty_new_texts == 0:
                                    flash(f"Summary: loaded no new task texts for user {user.pretty_username}", "warning")
                                elif qty_new_texts == 1:
                                    flash(f"Summary: loaded only one new task text for user {user.pretty_username}", "info")
                                else:
                                    flash(f"Summary: loaded {qty_new_texts} new task texts for user {user.pretty_username}", "info")
                    else:
                        flash("Missing task texts JSON filename", "warning")
                else:
                    flash("Missing task texts file (no JSON found)", "warning")
            else:  
                flash(f"Did not not load task texts for {user.pretty_username} because you did not explicity confirm it", "danger")
        else:
            flash_errors(form)
    texts_by_task_id=TaskText.get_dict_texts_by_task_id(user.id)
    most_recent_text_timestamp = None
    for t in texts_by_task_id:
        text = texts_by_task_id[t]
        most_recent_text_timestamp=most_recent_timestamp(
            most_recent_text_timestamp, texts_by_task_id[t].created_at
        )
        most_recent_text_timestamp=most_recent_timestamp(
            most_recent_text_timestamp, texts_by_task_id[t].modified_at
        )
    return render_template(
        "admin/user_text_load.html",
        user=user,
        qty_texts=len(texts_by_task_id),
        upload_text_form=UploadTaskTextsForm(),
        most_recent_text_timestamp=most_recent_text_timestamp,
    )
