# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
import os # for path
import re
import csv
from flask import abort, flash, request, redirect, Markup, url_for, current_app, render_template
from wtforms import ValidationError
from functools import wraps, update_wrapper
from flask_login import current_user, logout_user
from buggy_race_server.config import ConfigSettingNames, ConfigSettings, ConfigTypes
from buggy_race_server.admin.models import Announcement, Setting, Task
from buggy_race_server.extensions import db, bcrypt
from sqlalchemy import bindparam, insert, update
from datetime import datetime, timezone
import subprocess

def refresh_global_announcements(app):
  app.config['CURRENT_ANNOUNCEMENTS'] = Announcement.query.filter_by(is_visible=True)

def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)

def warn_if_insecure():
  pass # TODO delegating this to (Cloudflare) host/DNS config, not application level

def join_to_project_root(*args, app=current_app):
    """Returns filename made absolute with current_app's root_path
       with optional path too. App available in case this is ever
       needed from (e.g.) utils running outwith a web request."""
    return os.path.join(*[os.path.dirname(current_app.root_path), *args])
  
def flash_suggest_if_not_yet_githubbed(function):
  @wraps(function)
  def wrapper():
    if current_user and not current_user.is_github_connected():
      flash(Markup(f"You haven't connected to GitHub yet. <a href='{url_for('user.settings')}'>Do it now!</a>"), "danger")
    return function()
  return wrapper

def is_authorised(form, field):
  """ check the auth code — required for some admin activities (mainly user registration)"""
  auth_code = current_app.config.get(ConfigSettingNames.AUTHORISATION_CODE.name)
  if auth_code is None:
    raise ValidationError("No authorisation code has been set: cannot authorise")
  if not bcrypt.check_password_hash(auth_code, field.data):
    raise ValidationError(f"You must provide a valid authorisation code")
  return True

def minimum_access_level(access_level):
    """ General access decorator for views — but consider using
      requires_staff or requires_admin instead """
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not (current_user and current_user.access_level >= access_level):
                abort(403)
            return function(*args, **kwargs)
        return decorated_function
    return decorator

def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not (current_user and current_user.is_administrator):
            abort(403)
        return function(*args, **kwargs)
    return wrapper

def staff_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not (current_user and current_user.is_staff):
            abort(403)
        return function(*args, **kwargs)
    return wrapper


# check current user is active: this catches (and logs out) a user who has been
# made inactive _during_ their session: need this so admin can (if needed) bump
# students off the server (even if they are currently logged in). An inactive
# user can't log back in (because login rejects attempts by inactive usernames).
def active_user_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user and not current_user.is_active:
            flash(f"User \"{current_user.pretty_username}\" is inactive", "danger")
            logout_user()
            return redirect(url_for("public.home"))
        return function(*args, **kwargs)
    return wrapper

def save_config_env_overrides_to_db(app):
    """ Saves each config setting that's in the app config into the database.
      This is specifically used when the app starts up, to save any settings
      that are being set by environment variables in the database _before_
      the app then loads the entire config — including defaults — back from
      the database. This mechanism allows ENV overriding of bad/broken config.
    """
    for name in app.config.get(ConfigSettings.ENV_SETTING_OVERRIDES_KEY):
        value = app.config.get(name) # expecting a value here
        if value is not None:
            set_and_save_config_setting(app, name, value)
            print(f"* written {name} config setting (from ENV) into database", flush=True)

def load_settings_from_db(app):
    """ Read settings from db and set the app's config appropriately.
        This is inefficient — we hit the database more than once — but it's only called
        during app startup, setup, or when settings are being explicitly changed.

        Note that, at startup, if there are ENV variables set for any config,
        those are written to the database _before_ this, which is how they 
        always override (and why we don't care if they are already set).

        Also, this includes non-persistent config settings
    """
    settings = Setting.query.all()
    names_found_in_db = [setting.id for setting in settings if ConfigSettings.is_valid_name(setting.id)]
    missing_settings = []
    for name in ConfigSettings.DEFAULTS.keys():
        if name not in names_found_in_db:
            # explicitly write the default value into the db for missing settings
            # This is only expected when the app first starts up: after that, the
            # config settings remain in the database
            missing_settings.append(
                {
                  "id": name,
                  "value": ConfigSettings.stringify(name, ConfigSettings.DEFAULTS[name])
                }
            )
    if missing_settings:
        db.session.execute(insert(Setting.__table__), missing_settings)
        db.session.commit()
        print(f"* inserted {len(missing_settings)} config settings (with default values) into database", flush=True)
        # now reload settings: this time it won't have any missing
        settings = Setting.query.all()

    for setting in settings:
        # set_config_value casts to correct type (e.g., bool/int/str)
        ConfigSettings.set_config_value(app, setting.id, setting.value)

    return Setting.get_dict_from_db(settings) # pass the settings back as a dict


def set_and_save_config_setting(app, name, value):
    # this changes the app's config setting and also saves that
    # change in the database.
    # This isn't used much because the admin settings page (the
    # way settings are usually changed) uses bulk updates because
    # the forms handle groups of settings.

    ConfigSettings.set_config_value(app, name, value)

    setting = db.session.query(Setting).filter_by(id=name).first()
    settings_table = Setting.__table__
    if setting is None: # not already in db? then make it
        db.session.execute(
          insert(settings_table),
          [ {"id": name, "value": value} ]
        )
    else:
        db.session.execute(
          update(settings_table)
            .where(settings_table.c.id == bindparam("name"))
            .values(value=bindparam("value")),
            [ {"name": name, "value": value} ]
        )
    db.session.commit()

def load_config_setting(app, name):
    """ loads config setting from database, and returns value """
    if setting := db.session.query(Setting).filter_by(id=name).first():
       ConfigSettings.set_config_value(app, name, setting.value)
       return app.config.get(name) # will have done type conversion too
    else:
       raise ValueError(f"bad config: {name}")

def stringify_datetime(dt, want_secs=True):
    """ fails silently, returning empty string, if it's not a date """
    date_str = ""
    format = "%Y-%m-%d %H:%M:%S" if want_secs else "%Y-%m-%d %H:%M"
    if dt:
        try:
            date_str = dt.strftime(format)
        except (ValueError, AttributeError):
            pass
    return date_str 

def prettify_form_field_name(name):
  """ for flash error messages (e.g., 'authorisation_code' become 'Authorisation Code') """
  return name.replace("_", " ").title()

def get_download_filename(filename, want_datestamp=False, timezone=timezone.utc):
  """ For download files, returns the filename with a slug/project prefix, if configured. """
  if want_datestamp:
    datestamp = datetime.now(timezone).strftime('%Y-%m-%d')
    parts = filename.rsplit(".", 1) # (filename, extension)
    if len(parts) == 2:
      filename = f"{parts[0]}-{datestamp}.{parts[1]}"
    else: # there was no extension (unexpected)
      filename = f"{filename}-{datestamp}"
  slug = current_app.config[ConfigSettingNames.PROJECT_SLUG.name]
  if not slug:
    code = current_app.config[ConfigSettingNames.PROJECT_CODE.name]
    slug = re.sub(r"\W+", "-", code.lower().strip())
    slug = re.sub(r"(^-+|-{2,}|-$)", "", slug)
  if slug:
    return f"{slug}-{filename}"
  else:
    return filename

def get_tasks_as_issues_csv(tasks, is_line_terminator_crlf=False):

    class CsvString(object):
      def __init__(self):
        self.rows = []
      def write(self, row):
          self.rows.append(row)
      def __str__(self):
        return "".join(self.rows) # CSV writer adds newline?

    line_terminator = "\r\n" if is_line_terminator_crlf else "\n"
    issues_str = CsvString()
    issue_writer = csv.writer(issues_str, lineterminator=line_terminator)
    any_newline = re.compile(r"\r?\n")
    for task in tasks:
      issue_writer.writerow(
         # row is: * task name (with title)
         #         * markdown description: problem + solution + link
        [
          f"{task.fullname} {task.title}",
          "\n\n".join([ # markdown: blank line between paras
            re.sub(any_newline, "\\n", task.problem_text),
            re.sub(any_newline, "\\n", task.solution_text),
            f"[{task.fullname}]({task.get_url(current_app.config)})"
          ]).replace("\n", "\\n")
        ]
      )
    return str(issues_str)

def publish_tech_notes(app=current_app):
    """ Runs pelican to generate the tech notes.
        Creates a pelican config file with "live" config settings (as
        JINJA_GLOBALS) that are passed into the build.
        Throws exceptions if anything goes wrong.
    """
    JINJA_GLOBAL_MATCH_RE = re.compile(
      # "SOME_SETTING": "some value"
      r'\s*"([A-Z_][A-Z0-9_]+)"\s*\:\s*"([^"]*)"'
    )
    EMPTY_LINE_RE = re.compile(r'^\s*(#.*)?$')
    full_pathname = join_to_project_root(
      app.config[ConfigSettingNames._TECH_NOTES_PATH.name],
      app.config[ConfigSettingNames._TECH_NOTES_CONFIG_FILE_NAME.name],
      app=app
    )
    conf_file_reader = open(full_pathname)
    lines = conf_file_reader.readlines()
    conf_file_reader.close()
    globals_start_on_line = 0
    globals_end_on_line = 0
    for i in range(len(lines)):
      stripped_line=lines[i].strip()
      if stripped_line.startswith("JINJA_GLOBALS"):
        i += 1
        while (
          (i < len(lines))
          and (
            re.match(JINJA_GLOBAL_MATCH_RE, lines[i])
            or re.match(EMPTY_LINE_RE, lines[i])
          )
        ):
          if not globals_start_on_line:
            globals_start_on_line = i
          if res := re.match(JINJA_GLOBAL_MATCH_RE, lines[i]):
            (name, _unused_value) = res.groups()
            dec = ConfigSettings.get_dict_declaration(name, app.config.get(name))
            lines[i] = f"    {dec}\n"
          i += 1
        globals_end_on_line = i
    if current_app.config[ConfigSettingNames.IS_ALL_CONFIG_IN_TECH_NOTES.name]:
      jinja_globals_lines = [] # ignore settings read: use all of them
      for name in ConfigSettings.DEFAULTS:
        dec = ConfigSettings.get_dict_declaration(name, app.config.get(name))
        jinja_globals_lines.append(f"    {dec}\n")
      lines = lines[:globals_start_on_line] + \
              jinja_globals_lines + \
              lines[globals_end_on_line:]
    live_filename = current_app.config[ConfigSettingNames._TECH_NOTES_CONFIG_LIVE_NAME.name]
    live_pathname = join_to_project_root(
      app.config[ConfigSettingNames._TECH_NOTES_PATH.name],
      live_filename,
      app=app
    )
    live_config_file = open(live_pathname, "w")
    live_config_file.writelines(lines)
    live_config_file.close()
    publish_conf_file = join_to_project_root(
      app.config[ConfigSettingNames._TECH_NOTES_PATH.name],
      app.config.get(ConfigSettingNames._TECH_NOTES_CONFIG_PUBLISH_NAME.name),
      app=app
    )
    output_path = join_to_project_root(
      app.config[ConfigSettingNames._PUBLISHED_PATH.name],
      app.config.get(ConfigSettingNames._TECH_NOTES_OUTPUT_DIR.name),
      app=app
    )
    content_path = join_to_project_root(
      app.config[ConfigSettingNames._TECH_NOTES_PATH.name],
      app.config.get(ConfigSettingNames._TECH_NOTES_CONTENT_DIR.name),
      app=app
    )
    keepfile = os.path.join(output_path, ".keep")
    has_keepfile = os.path.exists(keepfile)

    # cwd must be the pelican dir so that the imports work
    pelican_dir = join_to_project_root(
        app.config[ConfigSettingNames._TECH_NOTES_PATH.name],
        app=app
    )
    command_result = None
    error_msg = None
    try:
        command_result = subprocess.run(
          [
            "pelican",
            "-s", publish_conf_file,
            "-o", output_path,
            content_path
          ],
          cwd=pelican_dir,
          check=True,
          capture_output=True # throw exception if this goes wrong
        )
    except subprocess.CalledProcessError as e:
        error_msg = "Tech notes publication failed (using Pelican): see message in log"
    else:
        set_and_save_config_setting(
          app,
          name=ConfigSettingNames._TECH_NOTES_GENERATED_DATETIME.name,
          value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        )
    # there's a keepfile (for git) in the technotes output dir
    # Pelican has probably deleted it, so replace it
    if has_keepfile: open(keepfile, 'a').close()
    if error_msg:
        raise SystemError(error_msg)
    if command_result:
        try:
            msg = command_result.stdout.decode('utf-8')
        except Exception as e:
            msg = "(nothing)"
        return f"Pelican: {msg}"


def load_tasks_into_db(task_source_filename, app=None, want_overwrite=False):
    """Reads tasks from markdown file, and inserts into database.
    Database task table must be empty.
    App needed to here to update config record of tasks published (?)"""
    new_tasks = parse_task_markdown(task_source_filename)
    if Task.query.count():
        if want_overwrite:
            db.session.query(Task).delete()
            db.session.commit()
        else:
            raise ValidationError(
              "Database is not empty: missing \"want_overwrite\" argument "
              f"prevented loading any of the {len(new_tasks)} new ones")
    db.session.execute(insert(Task.__table__), new_tasks)
    db.session.commit()
    if app is not None:
        set_and_save_config_setting(
            app,
            ConfigSettingNames._TASKS_LOADED_DATETIME.name,
            datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        )
    return len(new_tasks)

def parse_task_markdown(task_source_filename):
    SECTION_NAMES = [
      name for name in Task.__table__.columns._data.keys()
      if name.endswith("_text")
    ]
    H1_PHASE_NAME_RE = re.compile(r"^#\s+(.*)")
    PHASE_NAME_RE = re.compile(r"(\d)-(\w+)")
    H2_TITLE_RE = re.compile(r"^##\s+(.*)")
    H3_TEXT_SECTION_RE = r"^###\s+(\w+)"
    _LINE_NO = "_line_no"

    task_file_reader = open(task_source_filename)
    markdown_lines = task_file_reader.readlines()
    task_file_reader.close()
    line_no = 0

    def make_section_name(string):
        section_name = f"{string.lower()}_text"
        if section_name not in SECTION_NAMES:
            raise ValueError(
              f"bad section name \"{string}\" found in task source file at line {line_no}"
            )
        return section_name

    def get_next_line():
      nonlocal line_no
      if line_no >= len(markdown_lines):
        return None
      else:
        line = markdown_lines[line_no]
        line_no += 1
        return line

    def validated_task(task):
        phase =  task.get('phase')
        name = task.get('name')
        if not (phase and name):
            loc = f"at line {task[_LINE_NO]}" if task.get(_LINE_NO) else f"before line {line_no}"
            raise ValueError(f"Task is missing phase and/or name {loc}")
        for section_name in SECTION_NAMES:
            if task.get(section_name) is None:
              raise ValueError(f"Task {phase}-{name} has no \"{section_name}\"")
            else:
              task[section_name] = task[section_name].strip()
        if _LINE_NO in task:
          del task[_LINE_NO]
        return task

    sort_position = 1000
    tasks = []
    task = {}
    line = get_next_line()
    while line:
        h1 = re.findall(H1_PHASE_NAME_RE, line)
        h2 = re.findall(H2_TITLE_RE, line)
        h3 = re.findall(H3_TEXT_SECTION_RE, line)
        if len(h1)==1:
            if matched := re.match(PHASE_NAME_RE, h1[0]):
                (task['phase'], task['name']) = matched.groups()
            task[_LINE_NO] = line_no
            task["sort_position"] = sort_position
            sort_position += 100
        elif len(h2)==1:
            task['title'] = h2[0].strip()
        elif len(h3)==1:
            section_name = make_section_name(h3[0])
            section_lines = []
            end_of_task = False
            line = get_next_line()
            while line and not end_of_task:
                h3 = re.findall(H3_TEXT_SECTION_RE, line)
                if not line.startswith("#"):
                    section_lines.append(line)
                    line = get_next_line()
                else: # end of a section
                    task[section_name] = "".join(section_lines)
                    if len(h3)==1: # new section
                        section_name = make_section_name(h3[0])
                        section_lines = []
                        line = get_next_line()
                    else:
                        end_of_task = True
            if not end_of_task: # was end of file: keep last section
                task[section_name] = "".join(section_lines)
            tasks.append(validated_task(task))
            task = {}
            continue # already read
        line = get_next_line()
    if not tasks:
        raise ValueError("No tasks found")
    return tasks

def publish_task_list(app=current_app):
    # render the tasklist template and save it as _task_list.html
    tasks_by_phase = Task.get_dict_tasks_by_phase(want_hidden=False)
    qty_tasks = sum(len(tasks_by_phase[phase]) for phase in tasks_by_phase)
    created_at = datetime.now(timezone.utc)
    html = render_template(
        "public/project/_tasks.html",
        poster_word = app.config[ConfigSettingNames.PROJECT_REPORT_TYPE.name],
        project_code = app.config[ConfigSettingNames.PROJECT_CODE.name],
        expected_phase_completion = app.config[ConfigSettingNames.PROJECT_PHASE_MIN_TARGET.name],
        tasks_by_phase = tasks_by_phase,
        qty_tasks=qty_tasks,
        created_at=datetime.now(app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name]),
        is_storing_texts=app.config[ConfigSettingNames.IS_STORING_STUDENT_TASK_TEXTS.name],
    )
    task_list_filename = app.config[ConfigSettingNames._TASK_LIST_HTML_FILENAME.name]
    generated_task_file = join_to_project_root(
        app.config[ConfigSettingNames._PUBLISHED_PATH.name],
        task_list_filename
    )
    task_list_html_file = open(generated_task_file, "w")
    task_list_html_file.write(html)
    task_list_html_file.close()
    set_and_save_config_setting(
        app,
        name=ConfigSettingNames._TASK_LIST_GENERATED_DATETIME.name,
        value=stringify_datetime(created_at),
    )

def publish_tasks_as_issues_csv(app=current_app):
    generated_issuefile = join_to_project_root(
        app.config[ConfigSettingNames._PUBLISHED_PATH.name],
        app.config[ConfigSettingNames._BUGGY_EDITOR_ISSUES_FILE.name]
    )
    csv = get_tasks_as_issues_csv(
      Task.query.filter_by(is_enabled=True).order_by(Task.phase.asc(), Task.sort_position.asc()).all(),
      is_line_terminator_crlf=app.config[ConfigSettingNames.IS_ISSUES_CSV_CRLF_TERMINATED.name]
    )
    issue_csv_file = open(generated_issuefile, "w")
    issue_csv_file.write(csv)
    issue_csv_file.close()


# get_flag_color_defs for handling pennant/flag display with 
# custom CSS and SVG masks
FLAG_COLOR_NAME_RE = re.compile(r"\W+")
FLAG_COLOR_VALUE_RE = re.compile(r"[^-a-zA-Z0-9_().,#]+")

def _get_flag_color(flag, want_secondary=False):
    try:
        fc = flag.flag_color_secondary if want_secondary else flag.flag_color
    except AttributeError:
        return None # flag item doesn't have a color
    fc = str(fc).strip()
    # it's possible for fc to be empty string: no definition
    return (
        fc,
        (
          f"flag-col-{re.sub(FLAG_COLOR_NAME_RE, '-', fc).strip('-')}",
          "{"+f"background-color:{re.sub(FLAG_COLOR_VALUE_RE, '', fc)};"+"}"
        )
      ) if fc else None
 
def get_flag_color_css_defs(buggy_data_list):
    """ Extract name:value pairs of CSS class definition for flag colours:
        The buggy_data_list might be from a Buggy model or a RaceResult:
        we're looking for flag_color, flag_color_secondary, and flag_pattern
        fields
        Also: this is dumbly de-tainting the color string by removing
        anything beyond: word, #hex, rgb(x.x, x.x, x.x)
        returns dictionary of class name : background colour defs
    """
    flag_colors = {}
    for flag in buggy_data_list:
        for want_secondary in [True, False]:
          if name_value := _get_flag_color(flag, want_secondary=want_secondary):
            flag_colors[name_value[0]] = name_value[1]
    return flag_colors

def get_pretty_approx_duration(secs):
    """ Make a pretty duration string"""
    if secs < 60:
        return "1 second" if secs == 1 else f"{secs} seconds"
    mins = int(secs/60)
    if mins < 60:
        return "1 minute" if mins == 1 else f"{mins} minutes"
    hours = int(mins/60)
    if hours < 24:
        return "1 hour" if hours == 1 else f"{hours} hours"
    days = int(hours/24)
    return "1 day" if days == 1 else f"{days} days"

def get_day_of_week(datestr):
    """ doing this silently-robustly (e.g. deadline dates might not exist)"""
    try:
        return datetime.strptime(datestr, "%Y-%m-%dT%H:%M").strftime("%A")
    except ValueError:
        return ""
