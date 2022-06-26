# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
    jsonify,
    current_app
)
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime

from buggy_race_server.extensions import login_manager
from buggy_race_server.public.forms import LoginForm
from buggy_race_server.user.forms import RegisterForm, BulkRegisterForm
from buggy_race_server.user.models import User
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.race.models import Race
from buggy_race_server.utils import flash_errors, warn_if_insecure

import os
import csv
import io # for CSV dump

from buggy_race_server.extensions import db

blueprint = Blueprint("public", __name__, static_folder="../static")

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    # current_app.logger.info("Hello from the home page!")
    warn_if_insecure()
    return render_template("public/home.html",
        editor_url=current_app.config['BUGGY_EDITOR_GITHUB_URL'],
        piazza_url=current_app.config['PIAZZA_URL'],
        moodle_url=current_app.config['MOODLE_URL']
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
            flash("OK, you're logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.submit_buggy_data")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/login.html", form=form)


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            rhul_username=form.rhul_username.data,
            email=form.email.data,
            password=form.password.data,
            is_student=form.is_student.data,
            notes=form.notes.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template(
        "public/register.html",
        form=form,
        has_auth_code=current_app.config["HAS_AUTH_CODE"]
    )

@blueprint.route("/admin/bulk-register/", methods=["GET", "POST"])
@login_required
def bulk_register():
    """Register multiple user."""
    if not current_user.is_buggy_admin:
      abort(403)
    if not current_app.config["HAS_AUTH_CODE"]:
      flash("Bulk registration is disabled: must set REGISTRATION_AUTH_CODE first", "danger")
      abort(401)
    form = BulkRegisterForm(request.form)
    if form.validate_on_submit():
        lines = form.userdata.data.splitlines()
        reader = csv.DictReader(lines, delimiter=',')
        qty_users = 0
        line_no = 0
        problem_lines = []
        clean_user_data = []
        if len(lines) < 2:
          flash("Need CSV with a header row, then at least one line of data", "danger")
        elif not ('username' in reader.fieldnames and 'rhul_username' in reader.fieldnames and 'password' in reader.fieldnames):
          flash("CSV header row did not contain 'username', 'rhul_username' and 'password'", "danger")
        else:
          for row in reader:
            line_no += 1
            # if len(row) != 3:
            #   problem_lines.append(line_no)
            #   continue
            username = row['username'].strip().lower() if 'username' in row else None
            rhul_username = row['rhul_username'].strip().lower() if 'rhul_username' in row else None
            email = row['email'].strip().lower() if 'email' in row else None
            password = row['password'].strip() if 'password' in row else None
            current_app.logger.info("{}, pw:{}".format(username, password))
            if password and len(password) >= 4: # passwords longer than 4
              qty_users += 1
              clean_user_data.append({'username': username, 'rhul_username': rhul_username, 'email': email, 'password': password})
            else:
              problem_lines.append("{}".format(line_no))
          if len(problem_lines) > 0:
            pl = "s" if len(problem_lines)>1 else ""
            flash("Bulk registration aborted with {} problem{}: see line{}: {}".format(
              len(problem_lines), pl, pl, ", ".join(map(str,problem_lines))), "danger")
          else:
            qty_fails = 0
            for user_data in clean_user_data:
              try:
                User.create(
                  username=user_data['username'],
                  rhul_username=user_data['rhul_username'],
                  email=user_data['email'],
                  password=user_data['password'],
                  active=True,
                )
              except Exception as e:
                qty_fails += 1
                flash("Error creating user {}: {}".format(user_data['username'], e.message), "danger")
            flash("Bulk registered {} users".format(qty_users-qty_fails), "warning")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template(
        "admin/bulk_register.html",
        form=form,
        has_auth_code=current_app.config["HAS_AUTH_CODE"]
    )


@blueprint.route("/specs/")
def showspecs():
    """Buggy specifications page."""
    return render_template("public/buggyspecs.html", 
      defaults=Buggy.DEFAULTS,
      data=Buggy.game_data
    )

@blueprint.route("/specs/data/<data_filename>")
@blueprint.route("/specs/data")
def showspecs_data(data_filename=""):
    """Buggy specifications: data page."""
    want_mass = request.args.get('extra')=="mass" 
    if data_filename == "types.json":
      return jsonify(Buggy.game_data)
    elif data_filename == "defaults.json":
      return jsonify(Buggy.DEFAULTS)
    elif data_filename != "":
        abort(404)
    return render_template("public/specs-data.html", 
      defaults=Buggy.DEFAULTS,
      data=Buggy.game_data,
      is_showing_mass=want_mass
    )


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)

@blueprint.route("/project/")
@blueprint.route("/project/task/<task_id>")
def show_project(task_id=None):
  """Redirect projects and tasks to GitHub pages"""
  url = current_app.config["GITHUB_PAGES_URL"]
  if not url.endswith("/"):
    url += "/"
  if task_id:
    task_id = task_id.lower()
    if not task_id.startswith("task-"):
      task_id = f"task-{task_id}"
    return redirect(f"{url}project/tasks/#{task_id}", code=301 )
  else:
    return redirect( url + "project/", code=301 )

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

@blueprint.route("/admin/users")
@blueprint.route("/admin/users/<data_format>")
@blueprint.route("/admin/")
@login_required
def admin(data_format=None):
    """Admin list-of-uses/students page (which is the admin home page too)."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      # want_detail shows all users (otherwise it's only students)
      want_detail = request.path == '/admin/users'
      users = User.query.all()
      users = sorted(users, key=lambda user: (not user.is_buggy_admin, user.username))
      students = [s for s in users if s.is_student]
      if data_format == "csv":
        si = io.StringIO()
        cw = csv.writer(si)
        col_names = [
          'username',
          'logged_in',
          'json_length',
          'json_upload_at',
          'github_username',
          'github_repo',
          'is_student',
          'is_active'
        ]
        cw.writerow(col_names)
        for s in students: # note: CSV is only students
          cw.writerow([
                  s.username,
                  s.pretty_login_at,
                  s.pretty_json_length,
                  s.pretty_uploaded_at,
                  s.github_username,
                  s.course_repository if s.has_course_repository() else None,
                  s.is_student,
                  s.is_active
                 ])
        output = make_response(si.getvalue())
        yyyy_mm_dd_today = datetime.now().strftime("%Y-%m-%d")
        output.headers["Content-Disposition"] = f"attachment; filename=users-{yyyy_mm_dd_today}.csv"
        output.headers["Content-type"] = "text/csv"
        return output
      else:
        return render_template("admin/users.html",
          want_detail = want_detail,
          editor_repo_name = current_app.config["BUGGY_EDITOR_REPO_NAME"],
          users = users,
          admin_usernames = current_app.config['ADMIN_USERNAMES_LIST'],
          qty_students = len(students),
          qty_students_logged_in = len([s for s in students if s.logged_in_at]),
          qty_students_active = len([s for s in students if s.is_active]),
          qty_students_github = len([s for s in students if s.github_username]),
          qty_students_uploaded_json = len([s for s in students if len(s.latest_json)>1]),
      )


@blueprint.route("/admin/buggies/")
@blueprint.route("/admin/buggies/<data_format>")
@login_required
def admin_list_buggies(data_format=None):
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

@blueprint.route("/admin/settings/")
@login_required
def admin_settings():
    """Admin settings check page."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      return render_template("admin/settings.html")

@blueprint.route("/buggy/")
@blueprint.route("/buggy/<username>")
@login_required
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

