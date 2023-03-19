# -*- coding: utf-8 -*-
"""Race model."""
import datetime as datetime
import os

# get the config settings (without the app context):
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
from flask import current_app
from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
)
from buggy_race_server.buggy.models import Buggy

class Race(SurrogatePK, Model):
    """A race."""

    def get_default_race_time():
        # two minutes to midnight ;-)
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        tomorrow = tomorrow.replace(hour=23, minute=58, second=0, microsecond=0)
        return tomorrow

    __tablename__ = "races"
    id = db.Column(db.Integer, primary_key=True)
    title = Column(db.String(80), unique=False, nullable=False, default="")
    desc = Column(db.Text(), unique=False, nullable=False, default="")
    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    start_at = Column(db.DateTime, nullable=False, default=get_default_race_time())
    cost_limit = db.Column(db.Integer(), default=ConfigSettings.DEFAULTS[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name])
    is_visible = db.Column(db.Boolean(), default=bool(ConfigSettings.DEFAULTS[ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name]))
    result_log_url = Column(db.String(255), unique=True, nullable=True)
    league = Column(db.String(32), unique=False, nullable=True, default="")
    results_uploaded_at = Column(db.DateTime, nullable=True)
    buggies_entered = db.Column(db.Integer, nullable=False, default=0)
    buggies_started = db.Column(db.Integer, nullable=False, default=0)
    buggies_finished = db.Column(db.Integer, nullable=False, default=0)
    buggies_csv_url = Column(db.String(255), nullable=True)
    race_log_url = Column(db.String(255), nullable=True)
    is_result_visible = db.Column(db.Boolean(), nullable=False, default=False)

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
        if self.league is None or self.league == "":
            self.league = current_app.config[ConfigSettingNames.DEFAULT_RACE_LEAGUE.name]

    def log_path(self):
        return os.path.join(self.league, self.start_at.strftime('%Y-%m-%d-%H-%M'))

    def slug(self):
        return self.start_at.strftime('%Y-%m-%d-%H-%M')

#      return f"{self.league}self.start_at.strftime('%Y-%m-%d-%H-%M')

class RaceResult(SurrogatePK, Model):
    """A buggy's race result 
    Note that this links to the user not the buggy, because buggy records are
    not constant: they can and will change between races (if you need to find
    the details of buggie at the time they were entered in a race, follow that
    race's buggies_csv_url).
    """
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flag_color = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_color"])
    flag_color_secondary = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_color_secondary"])
    flag_pattern = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_pattern"])
    cost = db.Column(db.Integer, nullable=True)
    race_position = db.Column(db.Integer, nullable=False, default=0)
    violations_str = db.Column(db.String(255), nullable=True)

