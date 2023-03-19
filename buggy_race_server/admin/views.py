# -*- coding: utf-8 -*-
"""Admin views/controllers."""
import csv
import io  # for CSV dump
import random  # for API tests
from datetime import datetime, timedelta
import os
from collections import defaultdict
import markdown
import re

from sqlalchemy.inspection import inspect

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
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import bindparam, insert, update

from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

from buggy_race_server.admin.forms import (
    AnnouncementActionForm,
    AnnouncementForm,
    ApiKeyForm,
    BulkRegisterForm,
    GeneralSubmitForm,
    GenerateTasksForm,
    SettingForm,
    SetupAuthForm,
    SetupSettingForm,
    SubmitWithAuthForm,
    TaskForm,
)
from buggy_race_server.admin.models import Announcement, AnnouncementType, TaskText, Setting, SocialSetting, Task
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.buggy.views import show_buggy as show_buggy_by_user
from buggy_race_server.config import ConfigSettingNames, ConfigSettings, ConfigTypes
from buggy_race_server.database import db
from buggy_race_server.extensions import csrf, bcrypt
from buggy_race_server.user.forms import UserForm
from buggy_race_server.user.models import User
from buggy_race_server.utils import (
    flash_errors,
    get_download_filename,
    get_tasks_as_issues_csv,
    join_to_project_root,
    load_config_setting,
    load_settings_from_db,
    load_tasks_into_db,
    prettify_form_field_name,
    publish_task_list,
    publish_tech_notes,
    refresh_global_announcements,
    set_and_save_config_setting,
    staff_only,
    admin_only,
    stringify_datetime,
)

blueprint = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
  static_folder="../static"
)

SETTING_PREFIX = "settings" # the name of settings subform

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
          if ConfigSettings.TYPES.get(name) == ConfigTypes.PASSWORD:
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
    if not is_in_setup_mode:
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
        flash(f"{prettify_form_field_name(fieldName)}: {err_msg}", "danger")

def setup_summary():
    """ If setup is complete, this summarises the current config and db state,
    and unlike the dashboard has some helpful suggestions as to what to do next."""
    if not current_user or not current_user.is_authenticated or not current_user.is_buggy_admin:
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
    for ann in current_app.config['CURRENT_ANNOUNCEMENTS']:
        if ann.type == AnnouncementType.LOGIN.value:
            qty_announcements_login += 1
        elif ann.type == AnnouncementType.TAGLINE.value:
            qty_announcements_tagline += 1
        else:
            qty_announcements_global += 1
    return render_template(
       "admin/setup_summary.html",
       institution_full_name=current_app.config[ConfigSettingNames.INSTITUTION_FULL_NAME.name],
       institution_home_url=institution_home_url,
       institution_short_name=current_app.config[ConfigSettingNames.INSTITUTION_SHORT_NAME.name],
       is_report=bool(report_type),
       is_showing_project_workflow=current_app.config[ConfigSettingNames.IS_SHOWING_PROJECT_WORKFLOW.name],
       is_student_using_github_repo=current_app.config[ConfigSettingNames.IS_STUDENT_USING_GITHUB_REPO.name],
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
  if setup_status >= qty_setup_steps:
    setup_status = 0
    set_and_save_config_setting(
      current_app,
      ConfigSettingNames._SETUP_STATUS.name,
      setup_status
    )
    flash("Setup complete: you can now publish tech notes, add/edit tasks, and register users", "success")
    return setup_summary()
  if setup_status == 1:
    form = SetupAuthForm(request.form)
    # here we grant this session (effectively, this user) setup status
    session[ConfigSettingNames._SETUP_STATUS.name] = setup_status
  else:
    # after initial setup (auth), user must be logged in
    if current_user.is_anonymous or not current_user.is_buggy_admin:
      admins = current_app.config[ConfigSettingNames.ADMIN_USERNAMES.name]
      flash(f"Setup is not complete: you must log in as an admin user ({admins}) to continue", "warning")
      logout_user()
      return redirect( url_for('public.login'))
    form = SetupSettingForm(request.form)
  if request.method == "POST":
      if form.validate_on_submit():
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
              latest_json="",
            )
            flash(f"Created new admin user \"{new_admin_username}\"", "info")
          admin_user.is_active = True
          admin_user.is_student = False
          admin_user.save()
          set_and_save_config_setting(
            current_app,
            ConfigSettingNames.ADMIN_USERNAMES.name,
            new_admin_username
          )
          setup_status += 1
          set_and_save_config_setting(
            current_app,
            ConfigSettingNames._SETUP_STATUS.name,
            setup_status
          )
          login_user(admin_user)
          admin_user.logged_in_at = datetime.now()
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

  group_name = ConfigSettings.SETUP_GROUPS[setup_status-1].name
  settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
  html_descriptions = { 
    setting: markdown.markdown(ConfigSettings.DESCRIPTIONS[setting])
    for setting in ConfigSettings.DESCRIPTIONS
  }
  social_settings = SocialSetting.get_socials_from_config(settings_as_dict, want_all=True)
  return render_template(
    "admin/setup.html",
    setup_group_description=ConfigSettings.SETUP_GROUP_DESCRIPTIONS[group_name],
    #group=ConfigSettings.GROUPS[group_name],
    setup_status=setup_status,
    qty_setup_steps=qty_setup_steps,
    form=form,
    group_name=group_name,
    SETTING_PREFIX=SETTING_PREFIX,
    groups=ConfigSettings.GROUPS,
    sorted_groupnames=[name.name for name in ConfigSettings.SETUP_GROUPS],
    settings=settings_as_dict,
    social_settings=social_settings,
    type_of_settings=ConfigSettings.TYPES,
    pretty_default_settings={
      name: ConfigSettings.prettify(name, ConfigSettings.DEFAULTS[name])
      for name in ConfigSettings.DEFAULTS
    },
    html_descriptions=html_descriptions,
    env_setting_overrides=current_app.config[ConfigSettingNames._ENV_SETTING_OVERRIDES.name].split(","),
  )

@blueprint.route("/", strict_slashes=False)
@login_required
@staff_only
def admin():
    TASK_NOTE_LENGTH_THRESHHOLD = 2 # texts shorter than this are not counted
    today = datetime.now().date()
    one_week_ago = today - timedelta(days=7)
    users = User.query.order_by(User.username).all()
    buggies = Buggy.query.all()
    students = [s for s in users if s.is_student]
    students_active = [s for s in students if s.is_active]
    students_logged_in_this_week = [s for s in students_active if s.logged_in_at and s.logged_in_at.date() >= one_week_ago]
    students_logged_in_today = [s for s in students_logged_in_this_week if s.logged_in_at.date() >= today]
    students_never_logged_in = [s for s in students_active if not s.logged_in_at ]
    students_uploaded_this_week = [s for s in students_active if s.uploaded_at and s.uploaded_at.date() >= one_week_ago]
    users_deactivated = [u for u in users if not u.is_active]
    admin_users = [u for u in users if u.is_active and u.is_buggy_admin]
    other_users = [u for u in users if u.is_active and not (u in students or u in admin_users)]
    tasks = Task.query.filter_by(is_enabled=True).order_by(Task.phase.asc(), Task.sort_position.asc()).all()
    qty_tasks = len(tasks)
    tasks_by_id = {task.id: task.fullname for task in tasks}
    qty_texts_by_task = defaultdict(int)
    qty_texts = 0
    if is_storing_texts := current_app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name]:
      # TODO counting all texts, not only those of enrolled active students
      texts = TaskText.query.all()
      qty_texts = len(texts)
      for text in texts:
         if len(text.text) > TASK_NOTE_LENGTH_THRESHHOLD:
            qty_texts_by_task[tasks_by_id[text.task_id]] += 1
    return render_template(
      "admin/dashboard.html",
      admin_users=admin_users,
      is_storing_texts=is_storing_texts,
      other_users=other_users,
      purge_form = GeneralSubmitForm(),
      qty_admin_users=len(admin_users),
      qty_buggies=len(buggies),
      qty_texts_by_task=qty_texts_by_task,
      qty_texts=qty_texts,
      qty_other_users=len(other_users),
      qty_students_active=len(students_active),
      qty_students_logged_in_this_week=len(students_logged_in_this_week),
      qty_students_logged_in_today=len(students_logged_in_today),
      qty_students_never_logged_in=len(students_never_logged_in),
      qty_students=len(students),
      qty_tasks=qty_tasks,
      qty_uploads_today=len([s for s in students_uploaded_this_week if s.uploaded_at.date() >= today]),
      qty_uploads_week=len(students_uploaded_this_week),
      qty_users_deactivated=len(users_deactivated),
      qty_users=len(users),
      students_active = students_active,
      students_logged_in_this_week=[s for s in students_logged_in_this_week if s not in students_logged_in_today],
      students_logged_in_today=students_logged_in_today,
      students_never_logged_in=students_never_logged_in,
      submission_deadline=current_app.config[ConfigSettingNames.PROJECT_SUBMISSION_DEADLINE.name],
      tasks=tasks,
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
    users = sorted(users, key=lambda user: (not user.is_buggy_admin, user.username))
    students = [s for s in users if s.is_student]
    qty_teaching_assistants = len([u for u in users if u.is_teaching_assistant])
    qty_admins = len([u for u in users if u.is_administrator])
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
      return render_template("admin/users.html",
        want_detail = want_detail,
        editor_repo_name = current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name],
        users = users,
        admin_usernames = ConfigSettings.admin_usernames_list(current_app),
        qty_admins=qty_admins,
        qty_teaching_assistants=qty_teaching_assistants,
        qty_students = len(students),
        qty_students_logged_in = len([s for s in students if s.logged_in_at]),
        qty_students_enabled = len([s for s in students if s.is_active]),
        qty_students_github = len([s for s in students if s.github_username]),
        qty_students_uploaded_json = len([s for s in students if len(s.latest_json)>1]),
        ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
        ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
        is_password_change_by_any_staff=current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name],
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
    if form.validate_on_submit():
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
              ext_username=row['ext_username'].strip().lower() if 'ext_username' in row else None,
              email=_csv_tidy_string(row, 'email', want_lower=True),
              password=_csv_tidy_string(row, 'password', want_lower=False),
              first_name=_csv_tidy_string(row, 'first_name', want_lower=False),
              last_name=_csv_tidy_string(row, 'last_name', want_lower=False),
              created_at=datetime.now(),
              is_active=True,
              is_student=True,
              latest_json="",
              comment=_csv_tidy_string(row, 'comment', want_lower=False),
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
        form=form,
        example_csv_data = [
          ",".join(csv_fieldnames),
          ",".join(User.get_example_data("ada", csv_fieldnames)),
          ",".join(User.get_example_data("chaz", csv_fieldnames)),
        ],
        csv_fieldnames=f"{csv_fieldnames} {current_app.config}"
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
      is_own_text=user.id == current_user.id,
      tasks_by_phase=Task.get_dict_tasks_by_phase(want_hidden=False),
      texts_by_task_id=texts_by_task_id,
      qty_texts=len(texts_by_task_id),
      ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
      ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
      is_password_change_by_any_staff=current_app.config[ConfigSettingNames.IS_TA_PASSWORD_CHANGE_ENABLED.name],
  )

# user_id may be username or id
@blueprint.route("/user/<user_id>/edit", methods=['GET','POST'])
@login_required
@admin_only
def edit_user(user_id):
  if not current_user.is_buggy_admin:
      abort(403)
  if str(user_id).isdigit():
    user = User.get_by_id(int(user_id))
  else:
    user = User.query.filter_by(username=user_id).first()
  if user is None:
    abort(404)
  form = UserForm(request.form, obj=user, app=current_app)
  if request.method == "POST":
    if form.validate_on_submit():
      user.comment = form.comment.data
      user.is_student = form.is_student.data
      user.is_active = form.is_active.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
          user.first_name = form.first_name.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name]:
          user.last_name = form.last_name.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name]:
          user.email = form.email.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_EXT_USERNAME.name]:
          user.ext_username = form.ext_username.data
      # if username wasn't unique, validation should have caught it
      user.username = form.username.data
      user.save()
      flash(f"OK, updated user {user.pretty_username}", "success")
      return redirect(url_for("admin.list_users"))
    else:
      flash(f"Did not update user {user.pretty_username}", "danger")
      flash_errors(form)
  return render_template(
    "admin/user_edit.html",
    form=form,
    user=user,
    ext_username_name=current_app.config[ConfigSettingNames.EXT_USERNAME_NAME.name],
    ext_username_example=current_app.config[ConfigSettingNames.EXT_USERNAME_EXAMPLE.name],
  )

@blueprint.route("/api-keys", methods=['GET','POST'], strict_slashes=False)
@login_required
@staff_only
def api_keys():
    users = User.query.all()
    users = sorted(users, key=lambda user: (not user.is_buggy_admin, user.username))
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
    return render_template("admin/api_key.html", form=form, users=users)

@blueprint.route("/api-test", methods=["GET"], strict_slashes=False)
@login_required
@staff_only
def api_test():
    return render_template("admin/api_test.html", random_qty_wheels=random.randint(1,100))

@blueprint.route("/buggies/<username>")
def show_buggy(username):
   """ Using the show_buggy code from Buggy, as that's common for non-admin too"""
   # note that show_buggy_by_user checks the admin status of the requestor
   return show_buggy_by_user(username=username)


@blueprint.route("/download/buggies/csv")
@login_required
@staff_only
def download_buggies():
    """Download buggies as CSV (only format supported at the moment)"""
    buggies = Buggy.get_all_buggies_with_usernames()
    si = io.StringIO()
    cw = csv.writer(si)
    col_names = [col.name for col in Buggy.__mapper__.columns]
    col_names.insert(1, 'username')
    cw.writerow(col_names)
    [cw.writerow([getattr(b, col) for col in col_names]) for b in buggies]
    filename = get_download_filename("buggies.csv", want_datestamp=True)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output

@blueprint.route("/buggies", strict_slashes=False)
@login_required
@staff_only
def list_buggies(data_format=None):
    """Admin buggly list."""
    return render_template(
        "admin/buggies.html",
        buggies=Buggy.get_all_buggies_with_usernames()
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
      if form.validate_on_submit():
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
    task_count = Task.query.filter_by(is_enabled=True).count()
    return render_template(
      "admin/settings.html",
      form=form,
      group_name=group_name,
      SETTING_PREFIX=SETTING_PREFIX,
      groups=ConfigSettings.GROUPS,
      sorted_groupnames=[name.name for name in ConfigSettings.SETUP_GROUPS],
      settings=settings_as_dict,
      social_settings=social_settings,
      type_of_settings=ConfigSettings.TYPES,
      pretty_default_settings={
        name: ConfigSettings.prettify(name, ConfigSettings.DEFAULTS[name])
        for name in ConfigSettings.DEFAULTS
      },
      html_descriptions=html_descriptions,
      env_setting_overrides=current_app.config[ConfigSettingNames._ENV_SETTING_OVERRIDES.name].split(","),
      tech_notes_timestamp=current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name],
      is_tasks_ok=task_count and current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
      is_tech_note_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
    )

@blueprint.route("/announcements", strict_slashes=False)
@login_required
@admin_only
def list_announcements():
    # only using the form for the CSRF token at this point
    form = AnnouncementActionForm(request.form)
    announcements = sorted(
      Announcement.query.all(),
      key=lambda announcement: (announcement.type, announcement.text)
    )
    has_example_already = bool(
       [ann for ann in announcements if ann.text == Announcement.EXAMPLE_ANNOUNCEMENT]
    )
    return render_template(
      "admin/announcements.html",
      announcements=announcements,
      form=form,
      example_form=None if has_example_already else GeneralSubmitForm(),
    )

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
      if form.validate_on_submit():
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
    want_to_publish = None
    if form.submit_hide.data:
      want_to_publish = False
    elif form.submit_publish.data:
      want_to_publish = True
    if want_to_publish is None:
      flash("Error: couldn't decide to publish or not", "danger")
    else:
      announcement = Announcement.query.filter_by(id=announcement_id).first()
      if announcement is None:
        flash("Error: coudldn't find announcement", "danger")
      else:
        announcement.is_visible = want_to_publish
        announcement.save()
        if want_to_publish:
          flash("OK, published an announcement", "success")
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
    if form.validate_on_submit():
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

@blueprint.route("/tech-notes/publish", methods=["POST"])
@admin_only
def tech_notes_publish():
   return tech_notes_admin()

@blueprint.route("/tech-notes", methods=["GET"], strict_slashes=False)
@login_required
@admin_only
def tech_notes_admin():
  error_msg = None
  form = SubmitWithAuthForm(request.form)
  if request.method == "POST":
    if form.validate_on_submit():
      try:
        publish_tech_notes(current_app)
      except Exception as e:
        error_msg = f"Problem publishing tech notes: {e}"
        flash(error_msg, "danger")
      else:
        flash("Re-generated tech notes OK", "success")
    else:
      flash_errors(form)
  return render_template(
    "admin/tech_notes.html",
    form=FlaskForm(request.form), # nothing except CSRF token
    key_settings=[
      ConfigSettingNames.BUGGY_EDITOR_GITHUB_URL.name,
      ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
      ConfigSettingNames.PROJECT_CODE.name,
      ConfigSettingNames.SOCIAL_0_NAME.name,
      ConfigSettingNames.SOCIAL_1_NAME.name,
      ConfigSettingNames.SOCIAL_2_NAME.name,
      ConfigSettingNames.SOCIAL_3_NAME.name,
    ],
    is_publishing_enabled=current_app.config[ConfigSettingNames.IS_TECH_NOTE_PUBLISHING_ENABLED.name],
    tech_notes_external_url=current_app.config[ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name],
    notes_generated_timestamp=current_app.config[ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name],
  )

@blueprint.route("/tasks/publish", methods=["POST"])
@login_required
@admin_only
def tasks_generate():
    form = GeneralSubmitForm(request.form) # no auth required
    if form.validate_on_submit():
        # render the template and save it as _task_list.html
        try:
            publish_task_list(current_app)
        except IOError as e:
            flash(f"Failed to create task list: problem with file: {e}", "danger")
        else:
            qty_tasks = Task.query.filter_by(is_enabled=True).count()
            if qty_tasks == 0:
                flash("Task list page has been generated but there are no unhidden tasks in the project yet!", "danger")
                flash("You should load some tasks into the database before the project can start", "warning")
            else:
                flash(f"OK, task list page has been generated with latest data ({qty_tasks} tasks)", "success")
    return redirect(url_for('admin.tasks_admin'))

@blueprint.route("/tasks/all", methods=["GET"], strict_slashes=False)
@login_required
@admin_only
def tasks_admin_all():
    return tasks_admin()

@blueprint.route("/tasks", methods=["GET", "POST"], strict_slashes=False)
@login_required
@admin_only
def tasks_admin():
    form = GenerateTasksForm(request.form)
    is_fresh_update = False
    want_all = request.path.endswith("all")
    if request.method == "POST":
        if form.validate_on_submit():
            if want_overwrite := form.is_confirmed.data:
                # TODO ensure path no affected by cwd elsewhere
                md_filename_with_path = "project/tasks.md"
                delete_path = None
                pretty_source = "default tasks"
                if "markdown_file" in request.files:
                    md_file = request.files['markdown_file']
                    if md_file.filename:
                        md_filename_with_path = os.path.join(
                            current_app.config['UPLOAD_FOLDER'],
                            secure_filename(md_file.filename)
                        )
                        md_file.save(md_filename_with_path)
                        delete_path = md_filename_with_path
                        pretty_source = "uploaded tasks"
                try:
                    qty_tasks_added = load_tasks_into_db(
                        join_to_project_root(md_filename_with_path),
                        app=current_app,
                        want_overwrite=want_overwrite,
                    )
                    flash(f"OK, put {qty_tasks_added} {pretty_source} into the database", "success")
                    is_fresh_update = True
                except Exception as e:
                    flash(f"Error parsing/adding tasks: {e}", "danger")
                if delete_path:
                    try:
                        os.unlink(delete_path)
                    except os.error as e:
                        # could sanitise this, but the diagnostic might be useful
                        flash(f"Problem deleting uploaded file: {e}", "warning")
            else:
                flash(f"Did not not load tasks because you did not explicity confirm it", "danger")
        else:
            flash_errors(form)
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
    return render_template(
        "admin/tasks.html",
        form=form,
        is_showing_all_tasks=want_all,
        is_fresh_update=is_fresh_update,
        tasks=tasks,
        qty_tasks=qty_tasks,
        qty_disabled_tasks=qty_disabled_tasks,
        tasks_loaded_at=current_app.config[ConfigSettingNames._TASKS_LOADED_DATETIME.name],
        key_settings=[
          ConfigSettingNames.BUGGY_RACE_SERVER_URL.name,
          ConfigSettingNames.IS_TASK_URL_WITH_ANCHOR.name,
          ConfigSettingNames.TECH_NOTES_EXTERNAL_URL.name,
        ],
        example_task=example_task,
        example_task_url=example_task_url,
        task_list_updated_timestamp=current_app.config[ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name],
        auto_republish_config_name=ConfigSettingNames.IS_STATIC_CONTENT_AUTOGENERATED.name,
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
        infile = open("project/tasks.md")
        payload = "".join(infile.readlines())
        infile.close()
        filename = get_download_filename(f"tasks-{type}.{format}", want_datestamp=False)
    elif type == CURRENT:
        tasks = Task.query.filter_by(is_enabled=True).order_by(
          Task.phase.asc(),
          Task.sort_position.asc()
        ).all()
        if format == FORMAT_CSV:
            payload = get_tasks_as_issues_csv(tasks)
        else:
            payload = "".join([task.raw_markdown for task in tasks if task.is_enabled])
        filename = get_download_filename(f"tasks-{type}.{format}", want_datestamp=True)
    return Response(
        payload,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename=\"{filename}\""}
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
        if form.validate_on_submit():
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
            return redirect(url_for('admin.tasks_admin'))
        else:
            flash_errors(form)
    return render_template(
      "admin/task_edit.html",
      form=form,
      task=task
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

@blueprint.route("/task-texts", methods=["GET"], strict_slashes=False)
@login_required
@staff_only
def task_texts():
    # FIXME if not current_user.is_buggy_admin:
    # FIXME     abort(403)
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
       "admin/task_texts.html",
       students=students,
       tasks=tasks,
       texts_by_username=texts_by_username,
       buggies_by_username=buggies_by_username
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
    database_url = current_app.config.get("DATABASE_URL")
    redacted_database_url = "(unavailable)"
    if current_app.config.get("DATABASE_URL"):
      DATABASE_RE = re.compile(r"^([^:]+:[^:]+:).*(@\w+.*)")
      if match := re.match(DATABASE_RE, database_url):
        redacted_database_url = f"{match[1]}******{match[2]}"
    return render_template(
       "admin/system.html",
       redacted_database_url=redacted_database_url,
       unexpected_config_settings=current_app.config[ConfigSettings.UNEXPECTED_SETTINGS_KEY],
    )