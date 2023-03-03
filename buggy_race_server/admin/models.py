# -*- coding: utf-8 -*-
"""Admin models: settings and announcements."""

from collections import defaultdict
from datetime import datetime
from enum import Enum
import re
import markdown

from buggy_race_server.database import Column, Model, SurrogatePK, db
from buggy_race_server.config import ConfigSettings, ConfigSettingNames

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
      """ Returns current config values from database """
      settings_as_dict = {}
      for setting in query_result:
        settings_as_dict[setting.id] = setting.value
      return settings_as_dict
  
    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)

class AnnouncementType(Enum):
    DANGER = 'danger'
    INFO = 'info'
    LOGIN = 'login'
    SPECIAL = 'special'
    TAGLINE = 'tagline'
    WARNING = 'warning'

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

    ANCHOR_PREFIX = "task-"
    FULLNAME_RE = re.compile(r"^(\d+)-([a-zA-Z][a-zA-Z0-9_]*)$")

    # replaces %KEY% with config setting
    CONFIG_EMBED_RE = re.compile(r"%s*([_A-Z][A-Z0-9_]+)\s*%")

    @staticmethod
    def _sub_config_in_text(config, text):
        def _config_sub(match):
            value = config.get(match.group(1))
            return value if value is not None else ""
        return re.sub(Task.CONFIG_EMBED_RE, _config_sub, text)

    @staticmethod
    def split_fullname(fullname):
      (phase, name) = (None, None)
      if fullname.startwith(Task.ANCHOR_PREFIX): # be forgiving...
          fullname = fullname[len(Task.ANCHOR_PREFIX):] # ...strip anchor
      if matched := re.match(Task.FULLNAME_RE, fullname):
          phase = int(matched.group(1))
          name = matched.group(2).upper()
      return (phase, name)
    
    @staticmethod
    def get_dict_tasks_by_phase(want_hidden=True):
        """Returns dict keyed on phase number containing lists of
           tasks (in task sort order)"""
        tasks = Task.query.order_by(
          Task.phase.asc(),
          Task.sort_position.asc()
        ).all()
        tasks_by_phase = defaultdict(list)
        for task in tasks:
            if task.is_enabled or want_hidden:
                tasks_by_phase[task.phase].append(task)
        return tasks_by_phase

    @property
    def raw_markdown(self):
        return f"""# {self.phase}-{self.name.upper()}

## {self.title}

### Problem

{self.problem_text}

### Solution

{self.solution_text}

### Hints

{self.hints_text}
"""
    
    @property
    def anchor(self):
        return f"{Task.ANCHOR_PREFIX}{self.fullname.lower()}"

    @property
    def fullname(self):
        return f"{self.phase}-{self.name}"

    def problem_html(self, config):
        return markdown.markdown(
            Task._sub_config_in_text(config, self.problem_text)
        )

    def solution_html(self, config):
        return markdown.markdown(
            Task._sub_config_in_text(config, self.solution_text)
        )

    def hints_html(self, config):
        return markdown.markdown(
            Task._sub_config_in_text(config, self.hints_text)
        )

    def get_url(self, config):
        tasks_url = config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name] \
            + "/project/tasks"
        if config[ConfigSettingNames.TASK_URLS_USE_ANCHORS.name]:
            return f"{tasks_url}#{self.anchor}"
        else:
            return f"{tasks_url}/{self.fullname.lower()}"

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
    sort_position = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)


class Note(SurrogatePK, Model):
    """Note by student recording how they approached/did a task"""

    @staticmethod
    def get_dict_notes_by_task_id(user_id):
        """Returns dict of notes keyed on task id"""
        return {
           note.task_id: note
           for note in Note.query.filter_by(user_id=user_id).all()
        }

    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    text = Column(db.Text(), unique=False, nullable=False, default="")

    __tablename__ = "notes"
    def __init__(self, **kwargs):
       """Create instance."""
       db.Model.__init__(self, **kwargs)