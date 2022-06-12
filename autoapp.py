# -*- coding: utf-8 -*-
"""Create an application instance."""
from buggy_race_server.app import create_app
from flask import request, redirect
import os

app = create_app()

# only force to HTTPS if we've explicitly set it
force_redirect = os.environ.get("FORCE_REDIRECT_HTTP_TO_HTTPS", False)
if force_redirect and force_redirect != "0":
    @app.before_request
    def before_request():
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

