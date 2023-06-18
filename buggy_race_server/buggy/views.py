# -*- coding: utf-8 -*-
"""Buggy views."""
import json
import string
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.user.models import User
from buggy_race_server.utils import flash_errors, active_user_required, get_flag_color_css_defs


blueprint = Blueprint("buggy", __name__, url_prefix="/buggy", static_folder="../static")

# if is_api responds differently
def handle_uploaded_json(form, user, is_api=False):
  # is_api validation doesn't work:
  # so we're checking buggy_json field explicitly before getting here
  if form.validate_on_submit() or is_api:
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
              flash("\"{}\" was ignored because it wasn't an integer".format(key), "warning")
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
                  flash("\"{}\" was ignored because it wasn't true or false".format(key), "warning")
              if not is_api and was_ok_boolean:
                flash(f"{key} wasn't a JSON boolean, but OK: \"{dirty_buggy_data[key]}\" accepted as {str(clean_buggy_data[key]).lower()}", "info")
        elif isinstance(Buggy.DEFAULTS[key], int):
          try:
            clean_buggy_data[key] = int(dirty_buggy_data[key])
          except ValueError:
            if not is_api:
              flash("\"{}\" was ignored because it wasn't an integer".format(key), "warning")
        else:
          dirty_buggy_data[key] = dirty_buggy_data[key].strip().lower()
          s = "#" if dirty_buggy_data[key].startswith("#") else ""
          STRING_CHARS = string.digits + string.ascii_letters
          s += "".join(c for c in dirty_buggy_data[key] if c in STRING_CHARS)
          if s == "":
            if not is_api:
              flash("\"{}\" was ignored because it didn't look right".format(key), "warning")
          else:
            # check lengths:
            if max_str_len := Buggy.STRING_COL_LENGTH.get(key):
                if len(s) > max_str_len:
                  s = s[:max_str_len]
                  if not is_api:
                    flash(f"\"{key}\" was truncated to {max_str_len} characters", "warning")
            clean_buggy_data[key] = s
      else:
        if not is_api:
          flash("Unrecognised setting \"{}\" was ignored {}".format(key, word_too), "warning")
          word_too = "too"
    if is_multi_buggy_suspected:
        flash("Maybe you tried to upload more than one buggy? You can only upload a single JSON object here!", "danger")
    qty_defaults = 0
    for field_name in Buggy.DEFAULTS:
      if field_name not in clean_buggy_data:
        clean_buggy_data[field_name] = Buggy.DEFAULTS[field_name]
        qty_defaults+=1
    if qty_defaults > 0:
      if not is_api:
        (s, was) = ("s", "were") if qty_defaults > 1 else ("", "was")
        flash("{} setting{} {} not specified and got default value{} instead".format(qty_defaults, s, was, s), "info")
    if 'buggy_id' not in clean_buggy_data:
      clean_buggy_data['buggy_id'] = 1 # TODO not sure
    users_buggy = Buggy.query.filter_by(user_id=user.id).first()
    if users_buggy is None:
      Buggy.create(user_id = user.id, **clean_buggy_data)
      if not is_api:
        flash("JSON data for your racing buggy saved OK", "success")
    else:
      for field_name in clean_buggy_data:
        setattr(users_buggy, field_name, clean_buggy_data[field_name])
      users_buggy.save()
      if not is_api:
        flash("JSON data for your racing buggy updated OK", "success")
    if is_api:
      return {"ok": "buggy updated OK"}
    else:
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
    return render_template("buggy/buggy.html",
        is_own_buggy=user==current_user,
        user=user,
        buggy=buggy,
        is_plain_flag=is_plain_flag,
        flag_color_css_defs=flag_color_css_defs,
    )
