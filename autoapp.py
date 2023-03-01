# -*- coding: utf-8 -*-
"""Create an application instance."""
from buggy_race_server.app import create_app
from buggy_race_server.utils import refresh_global_announcements
from flask import request, redirect
from buggy_race_server.config import ConfigSettingNames

app = create_app()

