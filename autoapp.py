# -*- coding: utf-8 -*-
"""Create an application instance."""
from buggy_race_server.app import create_app
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

