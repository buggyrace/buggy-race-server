# -*- coding: utf-8 -*-
"""Race forms."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateTimeField,
    FileField,
    HiddenField,
    IntegerField,
    StringField,
    TextAreaField,
)
from wtforms.validators import Length, NumberRange, Optional, DataRequired

from buggy_race_server.race.models import Race
from buggy_race_server.config import ConfigSettings

class RaceForm(FlaskForm):
    """Race form."""
    id = HiddenField()

    title = StringField(
        "Title", validators=[Optional(), Length(max=80)]
    )
    desc = TextAreaField(
        "Description", validators=[Optional(), Length(max=255)]
    )
    cost_limit = IntegerField(
        "Cost limit",
        validators=[Optional(), NumberRange(min=10, max=None)]
    )
    start_at = DateTimeField(
        "Race start time",
        format='%Y-%m-%dT%H:%M', # note: T is important!
        validators=[Optional()]
    )
    is_visible = BooleanField("Is visible?")
    is_result_visible = BooleanField("Are results visible?")
    results_uploaded_at = DateTimeField(
        "Results uploaded at",
        format='%Y-%m-%dT%H:%M', # note: T is important!
        validators=[Optional()]
    )
    result_log_url = StringField(
        "URL of result log", validators=[Optional(), Length(max=255)]
    )
    buggies_csv_url =StringField(
        "URL of buggies CSV", validators=[Optional(), Length(max=255)]
    )
    race_log_url = StringField(
        "URL of race log", validators=[Optional(), Length(max=255)]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RaceForm, self).__init__(*args, **kwargs)
        self.race = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RaceForm, self).validate()
        if not initial_validation:
            return False
        if self.start_at.data is None:
            self.start_at.data = Race.get_default_race_time()
        race_at_this_time = Race.query.filter_by(start_at=self.start_at.data).first()
        if race_at_this_time and self.id.data != str(race_at_this_time.id):
            self.start_at.errors.append("Already got a race starting at this time")
            return False
        return True


class RaceDeleteForm(FlaskForm):
    is_confirmed = BooleanField("Are you sure?")
  
    def __init__(self, *args, **kwargs):
        super(RaceDeleteForm, self).__init__(*args, **kwargs)
  
    def validate(self):
        return super(RaceDeleteForm, self).validate()


class RaceResultsForm(FlaskForm):
    results_json_file = FileField("JSON results file")
    is_ignoring_warnings = BooleanField("Ignore warnings?")

    def __init__(self, *args, **kwargs):
        super(RaceResultsForm, self).__init__(*args, **kwargs)

    def validate(self):
        return super(RaceResultsForm, self).validate()