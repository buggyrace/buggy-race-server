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
from wtforms.validators import DataRequired, Optional, ValidationError

from buggy_race_server.admin.models import AnnouncementType
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
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
    authorisation_code = PasswordField("Authorisation code",  [is_authorised])

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
      choices=[(t,t) for t in AnnouncementType]
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
        if (
            self.name.data == ConfigSettingNames.REGISTRATION_AUTH_CODE.name
            and self.value.data == ConfigSettings.DEFAULTS[ConfigSettingNames.REGISTRATION_AUTH_CODE.name]
        ):
            raise ValidationError(
                "You must change the auth code to be something other than "
                "its default ('factory') setting"
            )

    def validate(self):
        return super(ConfigSettingForm, self).validate()

class SettingForm(FlaskForm):
    group = HiddenField()
    setting_list = HiddenField()
    settings = FieldList(
        FormField(ConfigSettingForm),
        min_entries=1,
        max_entries=len(ConfigSettings.DEFAULTS)
    )
    # when changing the auth form, need the current auth code too
    authorisation_code = PasswordField("Authorisation code",  [Optional()])

    def __init__(self, *args, **kwargs):
        super(SettingForm, self).__init__(*args, **kwargs)

    def validate(self):
        return super(SettingForm, self).validate()

