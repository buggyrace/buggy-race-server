# -*- coding: utf-8 -*-
"""Admin views/controllers."""
import csv
import io  # for CSV dump
import random  # for API test
from datetime import datetime
from sqlalchemy import insert, String

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from buggy_race_server.admin.forms import (
    AnnouncementActionForm,
    AnnouncementForm,
    ApiKeyForm,
    BulkRegisterForm,
)

from buggy_race_server.admin.models import Announcement
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.database import db
from buggy_race_server.user.models import User
from buggy_race_server.utils import flash_errors, refresh_global_announcements

blueprint = Blueprint("admin", __name__, url_prefix="/admin", static_folder="../static")

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

@blueprint.route("/")
def admin():
    # for now the admin home page lists the students on the basis it's the
    # most useful day-to-day admin page... might change in future
    return list_users(want_detail=False)

@blueprint.route("/users")
@blueprint.route("/users/<data_format>")
@login_required
def list_users(data_format=None, want_detail=True):
    """Admin list-of-uses/students page (which is the admin home page too)."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      # want_detail shows all users (otherwise it's only students)
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
    """Register multiple users."""
    if not current_user.is_buggy_admin:
      abort(403)
    if not current_app.config["HAS_AUTH_CODE"]:
      flash("Bulk registration is disabled: must set REGISTRATION_AUTH_CODE first", "danger")
      abort(401)
    form = BulkRegisterForm(request.form)
    err_msgs = []
    if form.validate_on_submit():
        is_json = form.is_json.data
        lines = form.userdata.data.splitlines()
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
          for row in reader:
            line_no += 1
            new_user = User(
              username=row['username'].strip().lower() if 'username' in row else None,
              org_username=row['org_username'].strip().lower() if 'org_username' in row else None,
              email=_csv_tidy_string(row, 'email', want_lower=True),
              password=_csv_tidy_string(row, 'password', want_lower=False),
              first_name=_csv_tidy_string(row, 'first_name', want_lower=False),
              last_name=_csv_tidy_string(row, 'last_name', want_lower=False),
              created_at=datetime.now(),
              active=True,
              is_student=True,
              latest_json="",
              notes=_csv_tidy_string(row, 'notes', want_lower=False),
            )
            #current_app.logger.info("{}, pw:{}".format(username, password))
            if new_user.password and len(new_user.password) >= 4: # passwords longer than 4
              qty_users += 1
              clean_user_data.append(new_user.get_fields_as_dict())
            else:
              problem_lines.append(line_no)
          if len(problem_lines) > 0:
            pl = "s" if len(problem_lines)>1 else ""
            err_msgs.append("Bulk registration aborted with {} problem{}: see line{}: {}".format(
              len(problem_lines), pl, pl, ", ".join(map(str,problem_lines))))
          else:
            result = db.session.execute(
                insert(User.__table__),
                clean_user_data
                # %(username)s, %(org_username)s, %(email)s, %(password)s, %(created_at)s, %(first_name)s, %(last_name)s, %(active)s, %(is_admin)s, %(latest_json)s, %(is_student)s, %(notes)s)
            )
            db.session.commit()
            if not is_json:
                flash("Bulk registered {} users".format(qty_users), "warning")
        if is_json:
          if err_msgs:
            return Response("{'error': 'FIXME'}", status=401, mimetype="application/json")
          else:
            return Response('{"status": "OK"}', status=200, mimetype="application/json")
        else:
            for err_msg in err_msgs:
                flash(err_msg, "danger")
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

@blueprint.route("/announcements/")
@login_required
def list_announcements():
    # only using the form for the CSRF token at this point
    form = AnnouncementActionForm(request.form)
    if not current_user.is_buggy_admin:
      abort(403)
    announcements = Announcement.query.all()
    announcements = sorted(announcements, key=lambda announcement: (announcement.type, announcement.text))
    return render_template("admin/announcements.html", announcements=announcements, form=form)

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
    return render_template("admin/announcements.html", announcements=announcements, form=form)

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

