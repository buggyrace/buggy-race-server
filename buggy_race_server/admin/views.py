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
)
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime

from buggy_race_server.extensions import login_manager
from buggy_race_server.admin.forms import ApiKeyForm, BulkRegisterForm
from buggy_race_server.user.models import User
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.race.models import Race
from buggy_race_server.utils import flash_errors, warn_if_insecure

import csv
import io # for CSV dump
import random # for API test

from buggy_race_server.extensions import db

blueprint = Blueprint("admin", __name__, url_prefix="/admin", static_folder="../static")

def _user_summary(username_list):
    if len(username_list) == 1:
        return f"user '{username_list[0]}'"
    else:
        return f"{len(username_list)} users"

@blueprint.route("/users")
@blueprint.route("/users/<data_format>")
@blueprint.route("/")
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


@blueprint.route("/bulk-register/", methods=["GET", "POST"])
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
        elif not ('username' in reader.fieldnames and 'org_username' in reader.fieldnames and 'password' in reader.fieldnames):
          flash("CSV header row did not contain 'username', 'org_username' and 'password'", "danger")
        else:
          for row in reader:
            line_no += 1
            # if len(row) != 3:
            #   problem_lines.append(line_no)
            #   continue
            username = row['username'].strip().lower() if 'username' in row else None
            org_username = row['org_username'].strip().lower() if 'org_username' in row else None
            email = row['email'].strip().lower() if 'email' in row else None
            password = row['password'].strip() if 'password' in row else None
            current_app.logger.info("{}, pw:{}".format(username, password))
            if password and len(password) >= 4: # passwords longer than 4
              qty_users += 1
              clean_user_data.append({'username': username, 'org_username': org_username, 'email': email, 'password': password})
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
                  org_username=user_data['org_username'],
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

@blueprint.route("/settings/")
@login_required
def settings():
    """Admin settings check page."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      return render_template("admin/settings.html")
