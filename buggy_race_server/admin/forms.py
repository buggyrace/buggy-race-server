# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import (
    FieldList,
    BooleanField,
    IntegerField,
    Form,
    FormField,
    HiddenField,
    SelectField,
    SelectMultipleField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Optional, ValidationError, Length

from buggy_race_server.admin.models import AnnouncementType
from buggy_race_server.config import ConfigSettings, ConfigSettingNames, ConfigTypes
from buggy_race_server.utils import is_authorised


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ApiKeyForm(FlaskForm):
    """API secret form."""
    usernames = MultiCheckboxField('usernames', coerce=str, choices=[])
    submit_clear_keys = SubmitField(label='Clear API keys')
    submit_generate_keys = SubmitField(label='Generate API keys')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(ApiKeyForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form *manually* because couldn't get the MultiCheckboxField
           to work as expected via setup."""
        return True

class BulkRegisterForm(FlaskForm):
    """Bulk register form."""
    userdata = TextAreaField(
        f"Userdata (CSV including header)", validators=[DataRequired()]
    )
    auth_code = PasswordField("Authorisation code",  [is_authorised])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(BulkRegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(BulkRegisterForm, self).validate()
        return initial_validation

class AnnouncementForm(FlaskForm):
    text = TextAreaField("Message text", validators=[DataRequired()])
    type = SelectField(
      'Type',
      validators=[DataRequired()],
      choices=[(t.value,t.value) for t in AnnouncementType]
    )
    is_visible = BooleanField("Display now?")
    is_html = BooleanField("Allow HTML?")

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)

    def validate(self):
        return super(AnnouncementForm, self).validate()

class AnnouncementActionForm(FlaskForm):
    id = IntegerField(validators=[DataRequired()])
    submit_publish = SubmitField(label='publish')
    submit_hide = SubmitField(label='hide')
    submit_delete = SubmitField(label='Delete announcement')

    def __init__(self, *args, **kwargs):
        super(AnnouncementActionForm, self).__init__(*args, **kwargs)

    def validate(self):
        return super(AnnouncementActionForm, self).validate()

class ConfigSettingForm(Form):
    name = HiddenField("Config-Setting-Name")
    value = StringField("Config-Setting-Value", validators=[])

    def validate_value(self, value):
      """ config setting validation"""
      name = self.name.data
      data_type = ConfigSettings.TYPES.get(name)
      if data_type == ConfigTypes.BOOLEAN:
        if self.value.data not in ["0", "1"]:
          raise ValidationError(f"{name} must be 1 or 0")
        return int(self.value.data) # use 1 or 0 (not bools) cos database is happier
      elif data_type == ConfigTypes.INT:
        if self.value.data and not str(self.value.data).isdigit():
          raise ValidationError(f"{name} must be a number")
        return int(self.value.data)
      if self.name.data == ConfigSettingNames.REGISTRATION_AUTH_CODE:
        if len(self.name.data) < ConfigSettings.MIN_PASSWORD_LENGTH:
          raise ValidationError(f"{name} is too short: need at least {ConfigSettings.MIN_PASSWORD_LENGTH} characters")
      return self.value.data


    def validate(self):
        return super(ConfigSettingForm, self).validate()

class SetupSettingForm(FlaskForm):
    # same as SettingForm except: no authcode required
    group = HiddenField()
    setting_list = HiddenField()
    settings = FieldList(
        FormField(ConfigSettingForm),
        min_entries=1,
        max_entries=len(ConfigSettings.DEFAULTS)
    )

    def validate(self):
        return super(SetupSettingForm, self).validate()

    def __init__(self, *args, **kwargs):
        super(SetupSettingForm, self).__init__(*args, **kwargs)

class SettingForm(FlaskForm):
    group = HiddenField()
    setting_list = HiddenField()
    settings = FieldList(
        FormField(ConfigSettingForm),
        min_entries=1,
        max_entries=len(ConfigSettings.DEFAULTS)
    )
    auth_code = PasswordField("Authorisation code", [DataRequired(), is_authorised])

    def validate(self):
        return super(SettingForm, self).validate()

    def __init__(self, *args, **kwargs):
        super(SettingForm, self).__init__(*args, **kwargs)

class SetupAuthForm(FlaskForm):
    auth_code = PasswordField("Authorisation code", [DataRequired(), is_authorised])
    new_auth_code = PasswordField(
      "New auth code", 
      [DataRequired(), Length(min=ConfigSettings.MIN_PASSWORD_LENGTH)]
    )
    new_auth_code_confirm = PasswordField("New auth confirm", [Optional()])
    admin_username = StringField(
      "Admin username",
      [DataRequired(), Length(min=ConfigSettings.MIN_USERNAME_LENGTH, max=ConfigSettings.MAX_USERNAME_LENGTH)])
    admin_password = PasswordField(
      "Admin user password",
      [DataRequired(), Length(min=ConfigSettings.MIN_PASSWORD_LENGTH)]
    )
    admin_password_confirm = PasswordField("Admin password confirm", [Optional()])

    def validate_new_auth_code(self, value):
      if self.new_auth_code.data == ConfigSettings.DEFAULTS[ConfigSettingNames.REGISTRATION_AUTH_CODE.name]:
        raise ValidationError(
          "You must change the auth code to be something other than "
          "its default ('factory') setting"
        )

    def validate_new_auth_code_confirm(self, value):
      """ TODO confirmation inputs are not in the forms yet"""
      if (
        self.new_auth_code_confirm.data != ""
        and self.new_auth_code_confirm.data != self.new_auth_code.data
      ):
        raise ValidationError("New auth code and its confirmation were not the same")

    def validate_admin_password_confirm(self, value):
      """ TODO confirmation inputs are not in the forms yet"""
      if (
        self.admin_password_confirm.data != ""
        and self.admin_password_confirm.data != self.admin_password.data
      ):
        raise ValidationError("New admin password and its confirmation were not the same")

    def validate(self):
        return super(SetupAuthForm, self).validate()

    def __init__(self, *args, **kwargs):
        super(SetupAuthForm, self).__init__(*args, **kwargs)

