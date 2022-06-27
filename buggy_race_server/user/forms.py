# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, PasswordField, StringField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from .models import User

# get the config settings (without the app context):
from buggy_race_server.config import ConfigFromEnv as config

# prevent unauthorised registration if there is an auth code in the environment
def is_authorised(form, field):
  auth_code = config.REGISTRATION_AUTH_CODE
  if auth_code is not None and field.data.lower() != auth_code.lower():
    raise ValidationError("You must provide a valid authorisation code")


class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    org_username = StringField(
        f"{config.INSTITUTION_SHORT_NAME} Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email", validators=[Email(), Length(min=6, max=80)]
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
    username = StringField(
        "Username", validators=[Optional(), Length(min=3, max=80)]
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


class BulkRegisterForm(FlaskForm):
    """Bulk register form."""
    userdata = TextAreaField(
        "Userdata (username, org_username, password)", validators=[DataRequired()]
    )
    authorisation_code = StringField("Authorisation code",  [is_authorised])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(BulkRegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(BulkRegisterForm, self).validate()
        return initial_validation
