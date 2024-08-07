# -*- coding: utf-8 -*-
"""API views."""

import json
from datetime import datetime, timezone, timedelta

from flask import Blueprint, Response, request, current_app, render_template

from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.views import handle_uploaded_json
from buggy_race_server.user.models import User
from buggy_race_server.config import ConfigSettingNames

blueprint = Blueprint("api", __name__, url_prefix="/api", static_folder="../static")

API_SECRET_LIFESPAN_MINS = 60

def get_json_error_response(msg, status=401):
  response = Response(
    '{"error": "' + msg + '"}',
    status=status,
    mimetype="application/json"
  )
  response.headers.add("Access-Control-Allow-Origin", "*") # CORS
  return response

@blueprint.route("/", methods=["GET"], strict_slashes=False)
def describe_api():
  return render_template(
    "public/api.html",
    api_task_name=current_app.config[ConfigSettingNames.TASK_NAME_FOR_API.name],
    buggy_race_server_url=current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name],
  )

@blueprint.route("/upload", methods=["POST", "OPTIONS"], strict_slashes=True)
def create_buggy_with_json_via_api():
  """ API call  """
  # basic API call to /api/upload with four params:
  #        user (the username for the user whose buggy to use)
  #        key (the API key for this user)
  #        secret (must match recent secret)
  #        buggy_json
  #
  if request.method == "OPTIONS":
      # CORS preflight enquiry
      # wildcards are OK here because the API is stateless so isn't
      # handling cookies: auth is provided in the data payload
      response = Response(status=204) # 204: no content
      response.headers.add("Access-Control-Allow-Origin", "*")
      response.headers.add("Access-Control-Allow-Headers", "*")
      response.headers.add("Access-Control-Allow-Methods", "POST")
      return response

  API_KEY_USER = "user"
  API_KEY_KEY = "key" # API key for the API key, heh
  API_KEY_SECRET = "secret"
  API_KEY_JSON = "buggy_json"

  username = ""
  buggy_json = ""
  if API_KEY_USER in request.form:
    username = request.form[API_KEY_USER].strip()
  if not username:
    return get_json_error_response("missing user")

  if API_KEY_KEY in request.form:
    api_key = request.form[API_KEY_KEY].strip()
  if not api_key:
    return get_json_error_response("missing API key")

  if API_KEY_SECRET in request.form:
    secret = request.form[API_KEY_SECRET].strip()
  if not secret:
    return get_json_error_response("missing secret")
  if API_KEY_JSON in request.form:
    buggy_json = request.form[API_KEY_JSON].strip()
  if not buggy_json:
    return get_json_error_response(f"no JSON ({API_KEY_JSON}) provided", status=200)
  user = User.query.filter_by(username=username).first()
  if user is None:
      return get_json_error_response("not authorised (bad user)")
  if user.api_key != api_key:
      return get_json_error_response("not authorised (wrong API key for this user)")
  if user.api_secret is None:
      return get_json_error_response("not authorised (missing secret)")
  if user.api_secret_at is None:
      return get_json_error_response("not authorised (missing secret timestamp)")
  if user.api_secret != secret:
      return get_json_error_response(f"not authorised (bad secret)")
  now_utc = datetime.now(timezone.utc)
  api_secret_at_utc = user.api_secret_at.replace(tzinfo=timezone.utc)
  try:
      delta_time_in_s = (now_utc - user.api_secret_at) / timedelta(seconds=1)
  except TypeError:
      delta_time_in_s = (now_utc - api_secret_at_utc) / timedelta(seconds=1)
  if delta_time_in_s > current_app.config[ConfigSettingNames.API_SECRET_TIME_TO_LIVE.name]:
      return get_json_error_response("not authorised (secret has expired)")
  if user.is_api_secret_otp:
      if user.api_secret_count > 0:
          return get_json_error_response("one-time secret has already been used")
      user.api_secret_count += 1
      user.save()
  # now send 200 even when response is an error (e.g., JSON parse fail)
  response = Response(
    json.dumps(handle_uploaded_json(BuggyJsonForm(request.form), user, True)),
    status=200,
    mimetype="application/json"
  )
  response.headers.add("Access-Control-Allow-Origin", "*") # CORS
  return response
