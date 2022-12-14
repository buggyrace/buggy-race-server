# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from buggy_race_server.config import ConfigSettings as configs
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.extensions import login_manager
from buggy_race_server.public.forms import LoginForm
from buggy_race_server.race.models import Race
from buggy_race_server.user.forms import RegisterForm
from buggy_race_server.user.models import User
from buggy_race_server.utils import flash_errors, warn_if_insecure, active_user_required

blueprint = Blueprint("public", __name__, static_folder="../static")

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))

@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    warn_if_insecure()
    return render_template("public/home.html")

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
    if not current_app.config[configs.USERS_HAVE_EMAIL]:
        del form.email
    if not current_app.config[configs.USERS_HAVE_FIRST_NAME]:
        del form.first_name
    if not current_app.config[configs.USERS_HAVE_LAST_NAME]:
        del form.last_name
    if not current_app.config[configs.USERS_HAVE_ORG_USERNAME]:
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
        has_auth_code=current_app.config[configs._HAS_AUTH_CODE]
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
    return render_template("public/specs_data.html", 
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
