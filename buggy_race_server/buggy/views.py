# -*- coding: utf-8 -*-
"""Buggy views."""
import json
import string
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.utils import flash_errors, active_user_required


blueprint = Blueprint("buggy", __name__, url_prefix="/buggies", static_folder="../static")

# if is_api responds differently
def handle_uploaded_json(form, user, is_api=False):
  # is_api validation doesn't work:
  # so we're checking buggy_json field explicitly before getting here
  if form.validate_on_submit() or is_api:
    user.latest_json = form.buggy_json.data
    user.uploaded_at = datetime.now()
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
    too = ""
    for key in dirty_buggy_data:
      if key == 'id': # user's buggy's id becomes buggy_id here
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
            clean_buggy_data[key] = s
      else:
        if not is_api:
          flash("Unrecognised setting \"{}\" was ignored {}".format(key, too), "warning")
          too = "too"
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
        flash("JSON buggy data saved OK", "success")
    else:
      for field_name in clean_buggy_data:
        setattr(users_buggy, field_name, clean_buggy_data[field_name])
      users_buggy.save()
      if not is_api:
        flash("JSON buggy data updated OK", "success")
    if is_api:
      return {"ok": "buggy updated OK"}
    else:
      return redirect(url_for("public.show_buggy"))
  else:
      flash_errors(form)
  if is_api:
      return {"error": "buggy data is missing"}
  else:
    return render_template("user/submit_buggy_data.html", form=form)

@blueprint.route("/json/", methods=["POST"])
@login_required
@active_user_required
def create_buggy_with_json():
    """Create or update user's buggy."""
    return handle_uploaded_json(BuggyJsonForm(request.form), current_user)

