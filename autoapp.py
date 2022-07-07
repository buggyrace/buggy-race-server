# -*- coding: utf-8 -*-
"""Create an application instance."""
from buggy_race_server.app import create_app
from buggy_race_server.utils import refresh_global_announcements
from flask import request, redirect
import os

app = create_app()

# only force to HTTPS if we've explicitly set it
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
    if app.config['CURRENT_ANNOUNCEMENTS'] is None:
        refresh_global_announcements(app, init=True)