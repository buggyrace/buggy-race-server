# -*- coding: utf-8 -*-
"""Race model."""
import datetime as dt
import os

from sqlalchemy import orm

from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
    reference_col,
    relationship,
)

# get the config settings (without the app context):
from buggy_race_server.init_config import ConfigFromEnv as config

class Race(SurrogatePK, Model):
    """A race."""

    DEFAULTS = {
        'cost_limit':      100,
        'is_visible':     True,
     }

    def get_default_race_time():
        # two minutes to midnight ;-)
        tomorrow = dt.datetime.today() + dt.timedelta(days=1)
        tomorrow = tomorrow.replace(hour=23, minute=58, second=0, microsecond=0)
        return tomorrow

    __tablename__ = "races"
    id = db.Column(db.Integer, primary_key=True)
    title = Column(db.String(80), unique=False, nullable=False, default="")
    desc = Column(db.Text(), unique=False, nullable=False, default="")
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    start_at = Column(db.DateTime, nullable=False, default=get_default_race_time())
    cost_limit = db.Column(db.Integer(), default=DEFAULTS['cost_limit'])
    is_visible = db.Column(db.Boolean(), default=DEFAULTS['is_visible'])
    result_log_url = Column(db.String(120), unique=True, nullable=True)
    league = Column(db.String(32), unique=False, nullable=True, default="")

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
        if self.league is None or self.league == "":
            self.league = config.RACE_LEAGUE

    def log_path(self):
        return os.path.join(self.league, self.start_at.strftime('%Y-%m-%d-%H-%M'))

    def slug(self):
        return self.start_at.strftime('%Y-%m-%d-%H-%M')

#      return f"{self.league}self.start_at.strftime('%Y-%m-%d-%H-%M')
    