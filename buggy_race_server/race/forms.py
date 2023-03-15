# -*- coding: utf-8 -*-
"""Race forms."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateTimeField,
    HiddenField,
    IntegerField,
    StringField,
    TextAreaField,
)
from wtforms.validators import Length, NumberRange, Optional

from buggy_race_server.race.models import Race


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
        race_at_this_time = Race.query.filter_by(start_at=self.start_at.data).first()
        if race_at_this_time and self.id.data != str(race_at_this_time.id):
            self.start_at.errors.append("Already got a race starting at this time")
            return False
        return True
