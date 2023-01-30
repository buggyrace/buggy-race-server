# -*- coding: utf-8 -*-
"""Admin models: settings and announcements."""

from datetime import datetime
from enum import Enum

from buggy_race_server.database import Column, Model, SurrogatePK, db

class SocialSetting():
  """A Social media link: note this is not a Flask/ORM model
     SOCIAL_n_NAME, SOCIAL_n_URL, SOCIAL_n_TEXT
  """

  MAX_SOCIALS = 4
  EMPTY_VALUE = "" # empty string, not None (so we can safely stringify them)

  @staticmethod
  def get_socials_from_config(conf, want_all=False):
    """ Get list of social site links from config (ignoring any with no name, unless want_all)"""
    socials = []
    for i in range(SocialSetting.MAX_SOCIALS):
      if want_all or conf.get(f"SOCIAL_{i}_NAME"):
        socials.append(
          SocialSetting(
            i,
            conf.get(f"SOCIAL_{i}_NAME") or SocialSetting.EMPTY_VALUE,
            conf.get(f"SOCIAL_{i}_URL") or SocialSetting.EMPTY_VALUE,
            conf.get(f"SOCIAL_{i}_TEXT") or SocialSetting.EMPTY_VALUE
         )
        )
    return socials

  def __str__(self):
    return f"<{self.index}: {self.name}, {self.url} [{self.text}]>"

  def __init__(self, index, name, url, text):
    self.index = index
    self.name = name
    self.url = url
    self.text = text


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


class Task(SurrogatePK, Model):
    """Task for students to complete."""

    def __str__(self):
        return f"{self.phase}-{self.name}"

    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(db.DateTime, nullable=True)
    phase = Column(db.Integer, nullable=False)
    name = Column(db.String(16), unique=False, nullable=False)
    title = Column(db.String(80), unique=False, nullable=False)
    problem_text = Column(db.Text(), unique=False, nullable=False, default="")
    solution_text = Column(db.Text(), unique=False, nullable=False, default="")
    hints_text = Column(db.Text(), unique=False, nullable=False, default="")
    is_enabled = db.Column(db.Boolean(), nullable=False, default=True)

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
