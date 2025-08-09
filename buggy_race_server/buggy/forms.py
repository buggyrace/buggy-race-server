# -*- coding: utf-8 -*-
"""Buggy forms."""

from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired, Length
from buggy_race_server.config import ConfigSettings

class BuggyJsonForm(FlaskForm):
    """Buggy (JSON) form."""

    buggy_json = TextAreaField(
        "JSON data", validators=[
            DataRequired(),
            Length(
                min=ConfigSettings.MIN_BUGGY_JSON_LENGTH,
                max=ConfigSettings.MAX_BUGGY_JSON_LENGTH
            )
        ]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(BuggyJsonForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(BuggyJsonForm, self).validate()
        if not initial_validation:
            return False
        # user = User.query.filter_by(username=self.username.data).first()
        # if user:
        #     self.username.errors.append("Username already registered")
        #     return False
        # user = User.query.filter_by(email=self.email.data).first()
        # if user:
        #     self.email.errors.append("Email already registered")
        #     return False
        return True
