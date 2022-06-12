# -*- coding: utf-8 -*-
"""Race forms."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, IntegerField, DateTimeField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length, Optional, NumberRange
import os

from .models import Race

class RaceForm(FlaskForm):
    """Race form."""

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
        format='%Y-%m-%d %H:%M',
        validators=[Optional()] # actually should be future
    )
    is_visible = BooleanField("Is visible?")

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
        if Race.query.filter_by(start_at=self.start_at.data).first():
            self.start_at.errors.append("Already got a race starting at this time")
            return False
        return True
