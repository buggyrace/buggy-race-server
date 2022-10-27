# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from wtforms import widgets, TextAreaField, PasswordField, StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from buggy_race_server.utils import is_authorised
from buggy_race_server.user.models import User

# get the config settings (without the app context):
from buggy_race_server.config import ConfigFromEnv as config

class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    org_username = StringField(
        f"{config.INSTITUTION_SHORT_NAME} Username",
        validators=[DataRequired(), Length(min=3, max=80)] if config.USERS_HAVE_ORG_USERNAME else []
    )
    email = StringField(
        "Email",
        validators=[Email(), Length(min=6, max=80)] if config.USERS_HAVE_EMAIL else []
    )
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(min=1, max=80)] if config.USERS_HAVE_FIRST_NAME else []
    )
    last_name = StringField(
        "Last name",
        validators=[DataRequired(), Length(min=1, max=80)] if config.USERS_HAVE_LAST_NAME else []
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=4, max=40)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    is_student = BooleanField(
        "Is an enrolled student?"
    )
    notes = TextAreaField(
        "Notes for staff", validators=[Optional(), Length(max=255)]
    )

    authorisation_code = StringField("Authorisation code",  [is_authorised])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""

        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        # user = User.query.filter_by(email=self.email.data).first()
        # if user:
        #     self.email.errors.append("Email already registered")
        #     return False
        return True

class ChangePasswordForm(FlaskForm):
    """Register form."""
    username = SelectField(
        "Username", validators=[Optional()], choices=[], validate_choice=False
    )
    password = PasswordField(
        "New password", validators=[DataRequired(), Length(min=4, max=40)]
    )
    confirm = PasswordField(
        "Verify new password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(ChangePasswordForm, self).validate()
        if not initial_validation:
            return False
        if self.username.data:
            user = User.query.filter_by(username=self.username.data).first()
            if not user:
                self.username.errors.append("User not found")
                return False
        return initial_validation

class ApiSecretForm(FlaskForm):
    """API secret form."""
    api_secret = StringField(
        "API secret", validators=[DataRequired(), Length(min=4, max=40)]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ApiSecretForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(ApiSecretForm, self).validate()
        if not initial_validation:
            return False
        return initial_validation
