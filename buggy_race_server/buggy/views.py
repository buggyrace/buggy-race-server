# -*- coding: utf-8 -*-
"""Buggy views."""
import json
import string
from datetime import datetime, timezone

from flask import (
  abort,
  Blueprint,
  current_app,
  flash,
  redirect,
  render_template,
  request,
  url_for,
)
from flask_login import current_user, login_required

from buggy_race_server.config import ConfigSettingNames
from buggy_race_server.admin.forms import SubmitWithConfirmForm
from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.user.models import User
from buggy_race_server.utils import flash_errors, active_user_required, get_flag_color_css_defs


blueprint = Blueprint("buggy", __name__, url_prefix="/buggy", static_folder="../static")

# if is_api responds differently
def handle_uploaded_json(form, user, is_api=False):
  # is_api validation doesn't work:
  # so we're checking buggy_json field explicitly before getting here
  if (form.is_submitted() and form.validate()) or is_api:
    user.latest_json = form.buggy_json.data
    user.uploaded_at = datetime.now(timezone.utc)
    user.save()
    try:
      dirty_buggy_data = json.loads(form.buggy_json.data)
    except json.decoder.JSONDecodeError as e:
      if is_api:
        return {"error": "Failed to parse JSON data"}
      else:
        flash("Failed to parse JSON data", "danger")
        flash(str(e), "warning")
        flash("No data was accepted", "info")
        return redirect(url_for("user.submit_buggy_data"))
    clean_buggy_data = {}
    word_too = ""
    is_multi_buggy_suspected = type(dirty_buggy_data) == list
    for key in dirty_buggy_data:
      key_type = type(key)
      if key_type != str:
          flash(f"Make sure your buggy JSON only contains keys which are strings: ignoring {key_type}", "warning")
          is_multi_buggy_suspected = is_multi_buggy_suspected or key_type in (dict, list)
      elif key == 'id': # user's buggy's id becomes buggy_id here
          try:
            clean_buggy_data['buggy_id'] = int(dirty_buggy_data[key])
          except ValueError:
            if not is_api:
              flash("Value for id was ignored because it wasn't an integer", "warning")
      elif key in Buggy.DEFAULTS:
        if Buggy.DEFAULTS[key] == False and isinstance(Buggy.DEFAULTS[key], bool):
            if isinstance(dirty_buggy_data[key], bool):
              clean_buggy_data[key] = int(dirty_buggy_data[key])
            else:
              dirty_buggy_data[key] = str(dirty_buggy_data[key]).strip().lower()
              was_ok_boolean = True
              if dirty_buggy_data[key] == 'true':
                clean_buggy_data[key] = True
              elif dirty_buggy_data[key] == 'false':
                clean_buggy_data[key] = False
              elif dirty_buggy_data[key] == "1":
                clean_buggy_data[key] = True
              elif dirty_buggy_data[key] == "0":
                clean_buggy_data[key] = False
              else:
                was_ok_boolean = False
                if not is_api:
                  flash(f"Value for {key} was ignored because it wasn't true or false", "warning")
              if not is_api and was_ok_boolean:
                flash(f"Value for {key} wasn't a JSON boolean, but OK: \"{dirty_buggy_data[key]}\" accepted as {str(clean_buggy_data[key]).lower()}", "info")
        elif isinstance(Buggy.DEFAULTS[key], int):
          try:
            clean_buggy_data[key] = int(dirty_buggy_data[key])
          except ValueError:
            if not is_api:
              flash(f"Value for {key} was ignored because it wasn't an integer", "warning")
        else:
          dirty_buggy_data[key] = str(dirty_buggy_data[key]).strip().lower()
          s = "#" if dirty_buggy_data[key].startswith("#") else ""
          STRING_CHARS = string.digits + string.ascii_letters
          s += "".join(c for c in dirty_buggy_data[key] if c in STRING_CHARS)
          if s == "":
              if not is_api:
                  flash(f"Value for {key} was ignored because it didn't have any alphanumeric characters in it", "warning")
          else:
            # check lengths:
            if max_str_len := Buggy.STRING_COL_LENGTH.get(key):
                if len(s) > max_str_len:
                  s = s[:max_str_len]
                  if not is_api:
                    flash(f"Value for {key} was truncated to {max_str_len} characters", "warning")
            if key in Buggy.GAME_DATA:
                if s not in Buggy.GAME_DATA[key]:
                    flash(f"Value for {key} was ignored because \"{s}\" is not a valid choice", "warning")
                else:
                    clean_buggy_data[key] = s # it's a value in a list 
            else:
                clean_buggy_data[key] = s # free-form string (e.g., flag_color)
      else:
        if not is_api:
          flash("Unrecognised setting \"{}\" was ignored {}".format(key, word_too), "warning")
          word_too = "too"
    if is_multi_buggy_suspected:
        flash("Maybe you tried to upload more than one buggy? You can only upload a single JSON object here!", "danger")
    qty_defaults = 0
    qty_explicits = 0
    for field_name in Buggy.DEFAULTS:
        if field_name in clean_buggy_data:
            qty_explicits += 1
        else:
            if field_name == "flag_color":
                clean_buggy_data[field_name] = current_app.config[
                    ConfigSettingNames.DEFAULT_FLAG_COLOR.name
                ]
            else:
                clean_buggy_data[field_name] = Buggy.DEFAULTS[field_name]
            qty_defaults += 1
    if qty_explicits == 0:
        msg = "Nothing to change: no buggy settings were found in the uploaded data"
        if is_api:
            return {"error": msg}
        flash(msg, "danger")
    else:
        (s, was) = ("s", "were") if qty_explicits > 1 else ("", "was")
        flash(f"{qty_explicits} setting{s} {was} specified", "info")
        if qty_defaults > 0:
            if not is_api:
                (s, was) = ("s", "were") if qty_defaults > 1 else ("", "was")
                flash(f"{qty_defaults} setting{s} {was} not specified and got default value{s} instead", "info")
        if 'buggy_id' not in clean_buggy_data:
            clean_buggy_data['buggy_id'] = 1 # TODO not sure
        users_buggy = Buggy.query.filter_by(user_id=user.id).first()
        if users_buggy is None:
            Buggy.create(user_id = user.id, **clean_buggy_data)
            if is_api:
                return {"ok": "buggy created OK"}
            flash("JSON data for your racing buggy saved OK", "success")
        else:
          for field_name in clean_buggy_data:
              setattr(users_buggy, field_name, clean_buggy_data[field_name])
          users_buggy.save()
          if not is_api:
              flash("JSON data for your racing buggy updated OK", "success")
        if is_api:
            return {"ok": "buggy updated OK"}
        if user == current_user:
            return redirect(url_for("buggy.show_own_buggy"))
        else:
            return redirect(url_for("admin.show_buggy", user_id=user.username))
  else:
      flash_errors(form)
  if is_api:
      return {"error": "buggy data is missing"}
  else:
      return render_template("user/submit_buggy_data.html", form=form)

@blueprint.route("/json", methods=["POST"], strict_slashes=False)
@login_required
@active_user_required
def create_buggy_with_json():
    """Create or update user's buggy."""
    return handle_uploaded_json(BuggyJsonForm(request.form), current_user)

@blueprint.route("/", strict_slashes=False)
@login_required
@active_user_required
def show_own_buggy():
  return show_buggy(username=current_user.username)

def show_buggy(username=None):
    """Inspection of buggy for given user: used by admin and user"""
    if username is None or username == current_user.username:
        user = current_user
        username = user.username
    else:
        if not current_user.is_staff:
          abort(403)
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f"Cannot show buggy: no such user \"{username}\"", "danger")
            abort(404)
    buggy = Buggy.query.filter_by(user_id=user.id).first()
    is_plain_flag = True
    if buggy is None:
        flash("No buggy exists for this user", "danger")
    else:
        is_plain_flag = buggy.flag_pattern == 'plain'
    flag_color_css_defs = get_flag_color_css_defs([buggy])
    if buggy and (
      current_app.config[ConfigSettingNames.IS_BUGGY_DELETE_ALLOWED.name]
      or current_user.is_administrator
    ):
      delete_form = SubmitWithConfirmForm()
      if user == current_user:
          delete_form_action = url_for("buggy.delete_own_buggy")
      else:
          delete_form_action = url_for("admin.delete_buggy", user_id=user.id)
    else:
      delete_form = None
      delete_form_action = None
    return render_template(
        "buggy/buggy.html",
        buggy=buggy,
        delete_form=delete_form,
        delete_form_action=delete_form_action,
        flag_color_css_defs=flag_color_css_defs,
        is_own_buggy=user==current_user,
        is_plain_flag=is_plain_flag,
        user=user,
    )

@blueprint.route("/delete", methods=["POST"], strict_slashes=False)
@login_required
@active_user_required
def delete_own_buggy():
  return delete_buggy(username=current_user.username)


def delete_buggy(username=None):
    """Inspection of buggy for given user: used by admin and user"""
    if username is None or username == current_user.username:
        user = current_user
        username = user.username
    else:
        if not current_user.is_administrator:
          abort(403)
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f"Cannot delete buggy: no such user \"{username}\"", "danger")
            abort(404)
    buggy = Buggy.query.filter_by(user_id=user.id).first()
    if buggy is not None:
        form = SubmitWithConfirmForm(request.form)
        if form.is_submitted() and form.validate():
            buggy_desc = f"{user.pretty_username}'s buggy"
            if user == current_user:
                buggy_desc = "your buggy"
            if not form.is_confirmed.data:
                flash(
                    f"Did not not delete {buggy_desc}"
                    " because you did not explicity confirm it",
                    "danger"
                )
            else:
                buggy.delete()
                flash(f"OK, deleted {buggy_desc}", "success")
        else:
            flash("Problem with form: did not delete", "warning")
    if user == current_user:
        return redirect(url_for("buggy.show_own_buggy"))
    else:
        return redirect(url_for("admin.show_buggy", user_id=user.username))

