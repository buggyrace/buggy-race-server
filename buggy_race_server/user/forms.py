# -*- coding: utf-8 -*-
"""User forms."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, TextAreaField, PasswordField, StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from buggy_race_server.utils import is_authorised
from buggy_race_server.user.models import User

# get the config settings (without the app context):
from buggy_race_server.config import ConfigSettings as configs

class UserForm(FlaskForm):
    """User form (for editing user details)."""
    id = HiddenField(DataRequired())
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    # fields that aren't being used (because config says so)
    # are explicitly, dynamically removed from the form in the view:
    # so validators are only applied if the field is indeed enabled
    org_username = StringField(
        f"Organisation Username",
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email",
        validators=[Email(), Length(min=6, max=80)]
    )
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(min=1, max=80)]
    )
    last_name = StringField(
        "Last name",
        validators=[DataRequired(), Length(min=1, max=80)]
    )
    is_student = BooleanField(
        "Is an enrolled student?"
    )
    is_active = BooleanField(
        "Is active? (Users marked as inactive cannot login and are effectively suspended)"
    )
    notes = TextAreaField(
        "Notes for staff", validators=[Optional(), Length(max=255)]
    )
    authorisation_code = PasswordField("Authorisation code",  [is_authorised])

    def __init__(self, app=None, *args, **kwargs):
        """Create instance."""
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(UserForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user and int(user.id) != int(self.id.data):
            self.username.errors.append(f"Username \"{self.username}\" already registered")
            return False
        return True

# registration same as user form except needs password (and confirmation)
# and the username can never already exist
class RegisterForm(UserForm):
    """Register form."""
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=4, max=40)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )

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
