# -*- coding: utf-8 -*-
"""Admin views/controllers."""
import csv
import io  # for CSV dump
import random  # for API test
from datetime import datetime, timedelta

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
    url_for,
)
from flask_login import current_user, login_required, login_user
from sqlalchemy import bindparam, insert, update

from flask_wtf import FlaskForm

from buggy_race_server.admin.forms import (
    AnnouncementActionForm,
    AnnouncementForm,
    ApiKeyForm,
    BulkRegisterForm,
    SettingForm,
    SetupSettingForm,
    SetupAuthForm,
)
from buggy_race_server.admin.models import Announcement, Setting, SocialSetting
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.config import ConfigSettingNames, ConfigSettings, ConfigTypes
from buggy_race_server.database import db
from buggy_race_server.extensions import csrf
from buggy_race_server.user.forms import UserForm
from buggy_race_server.user.models import User
from buggy_race_server.utils import publish_tech_notes, load_tasks_into_db
from buggy_race_server.utils import (
    flash_errors,
    load_settings_from_db,
    prettify_form_field_name,
    refresh_global_announcements,
    set_and_save_config_setting,
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

@blueprint.route("/setup", methods=["GET", "POST"])
def setup():
  setup_status=current_app.config[ConfigSettingNames._SETUP_STATUS.name]
  if not setup_status:
    flash(
      "Setup is complete on this server (config settings "
      "can be edited from within admin instead)", "danger"
    )
    abort(404)
  setup_status = int(setup_status)
  qty_setup_steps = len(ConfigSettings.SETUP_GROUPS)
  if setup_status >= qty_setup_steps:
    setup_status = 0
    set_and_save_config_setting(
      current_app,
      ConfigSettingNames._SETUP_STATUS.name,
      setup_status
    )
    flash("Setup complete: you can now register users", "success")
    return redirect( url_for('public.home'))
  if setup_status == 1:
    form = SetupAuthForm(request.form)
  else:
    # after initial setup (auth), user must be logged in
    # TODO: so need to provide access to login in case the session gets broken
    if current_user.is_anonymous or not current_user.is_buggy_admin:
      flash("Setup is not complete: you must log in as an admin user to continue", "warning")
      return redirect( url_for('public.login'))
    form = SetupSettingForm(request.form)
  if request.method == "POST":
      if form.validate_on_submit():
        if setup_status == 1: # this updating auth and creating a new admin user
          set_and_save_config_setting(
            current_app,
            ConfigSettingNames.REGISTRATION_AUTH_CODE.name,
            form.new_auth_code.data
          )
          new_admin_username = form.admin_username.data.strip().lower()
          if admin_user := User.query.filter_by(username=new_admin_username).first():
              admin_user.set_password(form.admin_password.data)
              flash(f"updated existing admin user {new_admin_username}'s password", "warning")
          else:
            admin_user = User.create(
              username=new_admin_username,
              password=form.admin_password.data,
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
          flash(f"OK, you're logged in with admin username {new_admin_username}.", "success")
        else: # handle a regular settings update, which may also be part of setup
          if _update_settings_in_db(form):
            setup_status += 1
            set_and_save_config_setting(
              current_app,
              ConfigSettingNames._SETUP_STATUS.name,
              setup_status
            )
          else:
            # something wasn't OK, so don't save and move on
            # (the errors will have been explicitly flashed)
            pass
      else:
        _flash_errors(form)

  group_name = ConfigSettings.SETUP_GROUPS[setup_status-1].name
  settings_as_dict = Setting.get_dict_from_db(Setting.query.all())
  return render_template(
    "admin/setup.html",
    setup_status=setup_status,
    qty_setup_steps=qty_setup_steps,
    form=form,
    SETTING_PREFIX=SETTING_PREFIX,
    group_name=group_name,
    group_description=ConfigSettings.SETUP_GROUP_DESCRIPTIONS[group_name],
    settings_group=ConfigSettings.GROUPS[group_name],
    settings=settings_as_dict,
    social_settings = SocialSetting.get_socials_from_config(settings_as_dict, want_all=True),
    type_of_settings=ConfigSettings.TYPES,
    pretty_default_settings={name: ConfigSettings.prettify(name, ConfigSettings.DEFAULTS[name]) for name in ConfigSettings.DEFAULTS},
    descriptions=ConfigSettings.DESCRIPTIONS,
    env_setting_overrides=current_app.config[ConfigSettingNames._ENV_SETTING_OVERRIDES.name].split(","),
  )

@blueprint.route("/")
@login_required
def admin():
    # for now the admin home page lists the students on the basis it's the
    # most useful day-to-day admin page... might change in future
    if not current_user.is_buggy_admin:
      abort(403)
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
    return render_template(
      "admin/dashboard.html",
      students_active = students_active,
      qty_users=len(users),
      qty_students=len(students),
      qty_students_active=len(students_active),
      qty_buggies=len(buggies),
      qty_students_logged_in_today=len(students_logged_in_today),
      students_logged_in_today=students_logged_in_today,
      qty_students_logged_in_this_week=len(students_logged_in_this_week),
      students_logged_in_this_week=[s for s in students_logged_in_this_week if s not in students_logged_in_today],
      qty_students_never_logged_in=len(students_never_logged_in),
      students_never_logged_in=students_never_logged_in,
      qty_uploads_today=len([s for s in students_uploaded_this_week if s.uploaded_at.date() >= today]),
      qty_uploads_week=len(students_uploaded_this_week),
      users_deactivated=users_deactivated,
      qty_users_deactivated=len(users_deactivated),
      admin_users=admin_users,
      qty_admin_users=len(admin_users),
      other_users=other_users,
      qty_other_users=len(other_users),
    )

@blueprint.route("/users")
@blueprint.route("/users/<data_format>")
@login_required
def list_users(data_format=None, want_detail=True, is_admin_can_edit=True):
    """Admin list-of-uses/students page (which is the admin home page too)."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      users = User.query.all()
      users = sorted(users, key=lambda user: (not user.is_buggy_admin, user.username))
      students = [s for s in users if s.is_student]
      if data_format == "csv": # note: CSV is only students
        si = io.StringIO()
        cw = csv.writer(si)
        # To get the column names, use the current_user (admin) even though
        # we're not going to save the data (there might not be any students)
        cw.writerow(current_user.get_fields_as_dict_for_csv().keys())
        for s in students:
          cw.writerow(list(s.get_fields_as_dict_for_csv().values()))
        output = make_response(si.getvalue())
        yyyy_mm_dd_today = datetime.now().strftime("%Y-%m-%d")
        output.headers["Content-Disposition"] = f"attachment; filename=buggyrace-users-{yyyy_mm_dd_today}.csv"
        output.headers["Content-type"] = "text/csv"
        return output
      else:
        # TODO want_detail shows all users (otherwise it's only students)
        return render_template("admin/users.html",
          want_detail = want_detail,
          is_admin_can_edit = is_admin_can_edit,
          editor_repo_name = current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name],
          users = users,
          admin_usernames = ConfigSettings.admin_usernames_list(current_app),
          qty_students = len(students),
          qty_students_logged_in = len([s for s in students if s.logged_in_at]),
          qty_students_enabled = len([s for s in students if s.is_active]),
          qty_students_github = len([s for s in students if s.github_username]),
          qty_students_uploaded_json = len([s for s in students if len(s.latest_json)>1]),
      )


@blueprint.route("/bulk-register/", methods=["GET", "POST"])
@blueprint.route("/bulk-register/<data_format>", methods=["POST"])
@login_required
def bulk_register(data_format=None):
    """Register multiple users."""
    is_json = data_format == "json"
    if not current_user.is_buggy_admin:
      abort(403)
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
              org_username=row['org_username'].strip().lower() if 'org_username' in row else None,
              email=_csv_tidy_string(row, 'email', want_lower=True),
              password=_csv_tidy_string(row, 'password', want_lower=False),
              first_name=_csv_tidy_string(row, 'first_name', want_lower=False),
              last_name=_csv_tidy_string(row, 'last_name', want_lower=False),
              created_at=datetime.now(),
              is_active=True,
              is_student=True,
              latest_json="",
              notes=_csv_tidy_string(row, 'notes', want_lower=False),
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
                  # %(username)s, %(org_username)s, %(email)s, %(password)s, %(created_at)s, %(first_name)s, %(last_name)s, %(is_active)s, %(is_admin)s, %(latest_json)s, %(is_student)s, %(notes)s)
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
        "admin/bulk_register.html",
        form=form,
        example_csv_data = [
          ",".join(csv_fieldnames),
          ",".join(User.get_example_data("ada", csv_fieldnames)),
          ",".join(User.get_example_data("chaz", csv_fieldnames)),
        ],
        csv_fieldnames=f"{csv_fieldnames} {current_app.config}"
    )

# user_id may be username or id
@blueprint.route("/user/<user_id>", methods=['GET','POST'])
@login_required
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
      user.notes = form.notes.data
      user.is_student = form.is_student.data
      user.is_active = form.is_active.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_FIRST_NAME.name]:
          user.first_name = form.first_name.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_LAST_NAME.name]:
          user.last_name = form.last_name.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_EMAIL.name]:
          user.email = form.email.data
      if current_app.config[ConfigSettingNames.USERS_HAVE_ORG_USERNAME.name]:
          user.org_username = form.org_username.data
      # if username wasn't unique, validation should have caught it
      user.username = form.username.data
      user.save()
      flash(f"OK, updated user {user.username}", "success")
      return redirect(url_for("admin.list_users"))
    else:
      flash(f"Did not update user {user.username}", "danger")
      flash_errors(form)
  return render_template(
    "admin/user.html",
    form=form,
    user=user,
  )

@blueprint.route("/api-keys", methods=['GET','POST'])
@login_required
def api_keys():
    if not current_user.is_buggy_admin:
      abort(403)
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

@blueprint.route("/api-test", methods=["GET"])
@login_required
def api_test():
    if not current_user.is_buggy_admin:
      abort(403)
    return render_template("admin/api_test.html", random_qty_wheels=random.randint(1,100))


@blueprint.route("/buggies/")
@blueprint.route("/buggies/<data_format>")
@login_required
def list_buggies(data_format=None):
    """Admin buggly list."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      # TODO shockingly building my own join because somehow the SQLAlchemy
      # TODO relationship isn't putting User into the buggy. Don't look
      # TODO Used db.session with .joins and everything. Sigh.
      users_by_id = dict()
      users = User.query.all()
      for user in users:
        users_by_id[user.id] = user
      buggies = Buggy.query.all()
      for b in buggies:
        b.username = users_by_id[b.user_id].username
        b.pretty_username = users_by_id[b.user_id].pretty_username
      if data_format == "csv":
        si = io.StringIO()
        cw = csv.writer(si)
        col_names = [col.name for col in Buggy.__mapper__.columns]
        col_names.insert(1, 'username')
        cw.writerow(col_names)
        [cw.writerow([getattr(b, col) for col in col_names]) for b in buggies]
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=buggies.csv"
        output.headers["Content-type"] = "text/csv"
        return output
      else:
        return render_template("admin/buggies.html", buggies=buggies)

@blueprint.route("/settings/<group_name>", methods=['GET','POST'])
@blueprint.route("/settings/", methods=['GET','POST'])
@login_required
def settings(group_name=None):
    """Admin settings check page."""
    if not current_user.is_buggy_admin:
      abort(403)
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
      descriptions=ConfigSettings.DESCRIPTIONS,
    )

@blueprint.route("/announcements/")
@login_required
def list_announcements():
    # only using the form for the CSRF token at this point
    form = AnnouncementActionForm(request.form)
    if not current_user.is_buggy_admin:
      abort(403)
    announcements = sorted(
      Announcement.query.all(),
      key=lambda announcement: (announcement.type, announcement.text)
    )
    return render_template(
      "admin/announcements.html",
      announcements=announcements,
      form=form
    )

@blueprint.route("/announcement/<int:id>", methods=["GET", "POST"])
@blueprint.route("/announcement/", methods=["GET", "POST"])
@login_required
def edit_announcement(id=None):
    if not current_user.is_buggy_admin:
      abort(403)
    announcement = None
    is_visible = False
    is_html =  False
    if id:
      announcement = Announcement.query.filter_by(id=id).first()
      if announcement is None:
        flash(f"No such announcement (id={id})", "danger")
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
      "admin/edit_announcement.html", 
      form=form, 
      id=id,
      is_html=is_html,
      is_visible=is_visible,
      announcement=announcement,
      delete_form=delete_form
    )

@blueprint.route("/announcements/publish", methods=["POST"])
@login_required
def publish_announcement():
    if not current_user.is_buggy_admin:
      abort(403)
    form = AnnouncementActionForm(request.form)
    want_to_publish = None
    if form.submit_hide.data:
      want_to_publish = False
    elif form.submit_publish.data:
      want_to_publish = True
    if want_to_publish is None:
      flash("Error: couldn't decide to publish or not", "danger")
    else:
      announcement = Announcement.query.filter_by(id=form.id.data).first()
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

@blueprint.route("/annoucement/delete", methods=["POST"])
@login_required
def delete_announcement():
    if not current_user.is_buggy_admin:
      abort(403)
    form = AnnouncementActionForm(request.form)
    if form.submit_delete.data:
      announcement = Announcement.query.filter_by(id=form.id.data).first()
      if announcement is None:
        flash("Error: coudldn't find announcement to delete", "danger")
      else:
        announcement.delete()
        flash("OK, deleted announcement", "success")
        refresh_global_announcements(current_app)
    else:
      flash("Error: incorrect button wiring, nothing deleted", "danger")
    return redirect(url_for("admin.list_announcements"))

@blueprint.route("/tech-notes", strict_slashes=False, methods=["GET", "POST"])
@login_required
def tech_notes_admin():
  if not current_user.is_buggy_admin:
    abort(403)
  error_msg = None
  if request.method == "POST":
    try:
      publish_tech_notes(current_app)
    except Exception as e:
      error_msg = f"Problem publishing tech notes: {e}"
    if error_msg:
      flash(error_msg, "danger")
    else:
      flash("Re-generated tech notes OK", "success")
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
    notes_generated_timestamp=current_app.config[ConfigSettingNames.TECH_NOTES_GENERATED_DATETIME.name],

  )

@blueprint.route("/tasks", strict_slashes=False, methods=["GET"])
@login_required
def tasks_admin():
    try:
        load_tasks_into_db(
          current_app,
          "project/tasks.md", # TODO explicit path,
          want_overwrite=True, # TODO require confirmation in form
        )
        flash("FIXME did task test OK", "success")
    except Exception as e:
        flash(f"FIXME task error: {e}", "danger")
    return redirect( url_for('admin.admin'))
