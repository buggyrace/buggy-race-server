# -*- coding: utf-8 -*-
"""Admin models: settings and announcements."""

from datetime import datetime
from enum import Enum

from buggy_race_server.config import ConfigSettings
from buggy_race_server.database import Column, Model, SurrogatePK, db

class Setting(SurrogatePK, Model):
    """A setting (for config)."""

    __tablename__ = "settings"
    id = Column(
      db.String(64),
      unique=True,
      nullable=False,
      primary_key=True,
    )
    value = Column(db.String(255), unique=False, nullable=False)

    def get_dict_from_db(query_result):
      settings_as_dict = {}
      for setting in query_result:
        settings_as_dict[setting.id] = setting.value
      return settings_as_dict
  
    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)

class AnnouncementType(Enum):
    INFO = 'info'
    WARNING = 'warning'
    SPECIAL = 'special'

class Announcement(SurrogatePK, Model):

    # this is an example announcement to populate the database with a demo
    # (only if there are no announcements already loaded)
    # Be careful with this: broken HTML here will cause problems!
    EXAMPLE_ANNOUNCEMENT = "<strong>BUGGY RACING IS CURRENTLY SUSPENDED</strong><br>pending the start of the new racing season"

    """An announcement to display on top of all pages."""

    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = Column(db.Text(), unique=False, nullable=False, default="")
    type = Column(db.String(32), unique=False, nullable=True)
    is_visible = db.Column(db.Boolean(), default=False)
    is_html = db.Column(db.Boolean(), default=False)
    
    def __init__(self, **kwargs):
      """Create instance."""
      db.Model.__init__(self, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Announcement({self.id!r} text:{self.text[0:16]}...)>"
