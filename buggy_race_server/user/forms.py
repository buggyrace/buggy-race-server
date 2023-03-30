# -*- coding: utf-8 -*-
"""User forms."""

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import HiddenField, TextAreaField, PasswordField, StringField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, ValidationError

from buggy_race_server.utils import is_authorised, prettify_form_field_name
from buggy_race_server.user.models import User
from buggy_race_server.config import ConfigSettings

class UserForm(FlaskForm):
    """User form (for editing user details)."""
    id = HiddenField(DataRequired())
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )

    # fields that aren't being used (because config says so)
    # are explicitly, dynamically removed from the form in the view
    # so they won't be submitted

    ext_username = StringField(f"External Username")
    email = StringField("Email")
    first_name = StringField("First name")
    last_name = StringField("Last name")
    is_student = BooleanField("Is an enrolled student?")
    is_active = BooleanField("Is active?")
    comment = TextAreaField("Comment", validators=[Optional(), Length(max=1024)])
    access_level = IntegerField("Staff role", validators=[Optional()])
    auth_code = PasswordField("Authorisation code",  [is_authorised])

    @staticmethod
    def is_mandatory_by_config(app, name, value):
        mandatory_fields = ConfigSettings.users_additional_fieldnames_is_enabled_dict(app)
        is_mandatory = mandatory_fields[name]
        if is_mandatory and (value is None or value == ""):
            raise ValidationError(f"missing {prettify_form_field_name(name)}, which is required by config settings")
        return is_mandatory

    @staticmethod
    def check_length(name, value, min=0, max=80):
        length = len(value)
        if length < min:
            raise ValidationError(f"{prettify_form_field_name(name)} is too short (at least {min} characters)")
        if length > max:
            raise ValidationError(f"{prettify_form_field_name(name)} is too long (at most {max} characters)")

    def validate_ext_username(self, field):
        value = field.data.strip()
        if UserForm.is_mandatory_by_config(current_app, field.name, value):
            UserForm.check_length(field.name, value, min=3, max=32)
        return value

    def validate_email(self, field):
        value = field.data.strip()
        if UserForm.is_mandatory_by_config(current_app, field.name, value):
            UserForm.check_length(field.name, value, min=3, max=32)
            if not '@' in value:
                raise ValidationError("Email must contain @-sign")
        return value

    def validate_first_name(self, field):
        value = field.data.strip()
        if UserForm.is_mandatory_by_config(current_app, field.name, value):
            UserForm.check_length(field.name, value, min=3, max=32)
        return value

    def validate_last_name(self, field):
        value = field.data.strip()
        if UserForm.is_mandatory_by_config(current_app, field.name, value):
            UserForm.check_length(field.name, value, min=3, max=32)
        return value

    def validate_access_level(self, field):
        if field.data not in [0, User.TEACHING_ASSISTANT, User.ADMINISTRATOR]:
            raise ValidationError("Access level not recognised")
        return field.data

    def validate(self):
        """Validate the form."""
        initial_validation = super(UserForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user and (not self.id.data or (int(user.id) != int(self.id.data))):
            self.username.errors.append(f"Sorry: \"{user.pretty_username}\" is already registered")
            return False
        return True

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = None

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
    """Change password form."""
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
    # auth_code here is — uniquely — optional, because it only applies
    # if the user is not the current_user (then: must be admin too)

    auth_code = PasswordField(
        """Authorisation code""",
        validators=[Optional(), Length(min=4, max=40)]
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
    is_one_time_password = BooleanField(
        "Is one-time password?", validators=[Optional()]
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
