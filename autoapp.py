# -*- coding: utf-8 -*-
"""Create an application instance."""
from buggy_race_server.app import create_app
from buggy_race_server.utils import refresh_global_announcements
from flask import request, redirect
from buggy_race_server.config import ConfigSettingNames

app = create_app()

SETUP_PATH = "/admin/setup"

# only force to HTTPS if we've explicitly set it
if "FORCE_REDIRECT_HTTP_TO_HTTPS" in app.config:
    if app.config["FORCE_REDIRECT_HTTP_TO_HTTPS"]:
        @app.before_request
        def before_request():
            if not request.is_secure:
                url = request.url.replace('http://', 'https://', 1)
                code = 301
                return redirect(url, code=code)

# the first request to the app loads the current announcements into the config
# thereafter it only gets updated if any announcements are published or hidden
# (trying to avoid a database read ever request)
@app.before_request
def load_announcements():
    if app.config.get(ConfigSettingNames._CURRENT_ANNOUNCEMENTS) is None:
        refresh_global_announcements(app)

@app.before_request
def check_setup_status():
    # TODO better to use Flask.static_folder_url (to get path if it's changed)
    #      ...but didn't get nice results: hardcoded for now
    if app.config.get(ConfigSettingNames._SETUP_STATUS) and not request.path.startswith(f"/static"):
        if request.path != SETUP_PATH:
            return redirect(f"{request.root_path}{SETUP_PATH}")

