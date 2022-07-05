# -*- coding: utf-8 -*-
"""API views."""

import json
from flask import Blueprint, request, Response, current_app
from flask_login import login_required, current_user
from flask_wtf import CSRFProtect
from datetime import datetime

blueprint = Blueprint("api", __name__, url_prefix="/api", static_folder="../static")

from buggy_race_server.user.models import User
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.buggy.forms import BuggyJsonForm
from buggy_race_server.buggy.views import handle_uploaded_json

API_SECRET_LIFESPAN_MINS = 60

@blueprint.route("/upload/", methods=["POST"])
def create_buggy_with_json_via_api():
  """ API call  """
  # basic API call to /api/upload with three params:
  #        user (the username for the user whose buggy to use)
  #        secret (must match recent secret)
  #        buggy_json
  #
  username = ''
  buggy_json = ''
  if "user" in request.form:
    username = request.form['user'].strip()
  if not username:
    return Response("{'error':'missing user'}", status=401, mimetype='application/json')

  if "key" in request.form:
    api_key = request.form['key'].strip()
  if not api_key:
    return Response("{'error':'missing API key'}", status=401, mimetype='application/json')

  if "secret" in request.form:
    secret = request.form['secret'].strip()
  if not secret:
    return Response("{'error':'missing secret'}", status=401, mimetype='application/json')
  if "buggy_json" in request.form:
    buggy_json = request.form['buggy_json'].strip()
  if not buggy_json:
    return Response("{'error':'no JSON (buggy_json) provided'}", status=401, mimetype='application/json')

  user = User.query.filter_by(username=username).first()
  if user is not None:
    if user.api_key != api_key:
      return Response("{'error':'not authorised (wrong API key for this user)'}", status=401, mimetype='application/json')
    if user.api_secret is not None and user.api_secret_at is not None:
      if user.api_secret != secret:
        return Response("{'error':'not authorised (bad secret)'}", status=401, mimetype='application/json')
      if (datetime.now() - user.api_secret_at).seconds/60 > API_SECRET_LIFESPAN_MINS:
        return Response("{'error':'not authorised (secret has expired)'}", status=401, mimetype='application/json')
      response_to_update = handle_uploaded_json(BuggyJsonForm(request.form), user, True)
      # note send 200 even if there was an error
      return Response(json.dumps(response_to_update), status=200, mimetype='application/json')
  return Response("{'error':'not authorised (bad user)'}", status=401, mimetype='application/json')
