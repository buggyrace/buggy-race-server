# -*- coding: utf-8 -*-
"""User models."""
import datetime as datetime
from random import randint
import re

from flask import current_app
from flask_login import UserMixin
from sqlalchemy import orm

# get the config settings (without the app context):
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
    reference_col,
    relationship,
)
from buggy_race_server.extensions import bcrypt
from buggy_race_server.lib.http import Http

API_KEY_LENGTH = 16

EXAMPLE_USER_DATA = {
    "ada": {
        "username": "ada",
        "password": "secR3t89o!W",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "ext_username": "al003",
        "email": "a.lovelace@example.com"
    },
    "chaz":{
        "username": "chaz",
        "password": "n-E7jWz*DIg",
        "first_name": "Charles",
        "last_name": "Babbage",
        "ext_username": "cb002",
        "email": "c.babbage@example.com"
    },
}

class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = "roles"
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref="roles")

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Role({self.name})>"


class User(UserMixin, SurrogatePK, Model):

    NO_STAFF_ROLE = 0
    TEACHING_ASSISTANT = 1
    ADMINISTRATOR = 9

    ROLE_NAMES = {
        NO_STAFF_ROLE: "Not staff",
        TEACHING_ASSISTANT: "Teaching Assistant",
        ADMINISTRATOR: "Administrator",
    }

    """A user of the app."""

    __tablename__ = "users"
    username = Column(db.String(80), unique=True, nullable=False)
    ext_username = Column(db.String(80), unique=True, nullable=True)
    email = Column(db.String(80), unique=True, nullable=True)
    #: The hashed password
    password = Column(db.LargeBinary(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    is_active = Column(db.Boolean(), default=True)
    is_admin = Column(db.Boolean(), default=False)
    access_level = Column(db.Integer, nullable=False, default=0)
    buggies = db.relationship("Buggy", backref="users", lazy=True)
    latest_json = Column(db.Text(), default="")
    github_username = Column(db.Text(), nullable=True)
    github_access_token = Column(db.Text(), nullable=True)
    is_student = Column(db.Boolean(), default=True)
    logged_in_at = Column(db.DateTime, nullable=True)
    uploaded_at = Column(db.DateTime, nullable=True)
    api_secret =  Column(db.String(30), nullable=True)
    api_secret_at = Column(db.DateTime, nullable=True)
    api_key = Column(db.String(30), nullable=True)
    comment = Column(db.Text(), default=False)

    def __init__(self, username, ext_username=None, email=None, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username.lower(), ext_username=ext_username, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None
        # disallow optional fields to be set unless they are explicitly enabled
        mandatory_fields = ConfigSettings.users_additional_fieldnames_is_enabled_dict(current_app)
        for fieldname in mandatory_fields:
            if not mandatory_fields[fieldname]:
                setattr(self, fieldname, None) # force None
        self.init_on_load()

    @orm.reconstructor
    def init_on_load(self):
        self._github = None
        self._has_course_repository = None

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    def generate_api_key(self, want_key):
        if want_key:
          self.api_key = "".join([f"{randint(0,15):0x}" for i in range(API_KEY_LENGTH)]).upper()
        else:
          self.api_key = None

    def get_fields_as_dict_for_insert(self):
        """ Fields needed to create (insert) new user (absent fields are defaulted) """
        return {
            'username': self.username,
            'ext_username': self.ext_username,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'latest_json': self.latest_json,
            'is_student': self.is_student,
            'comment': self.comment,
        }

    def get_fields_as_dict_for_csv(self):
        """ Fields used for saving to CSV """
        if self.github_username and self.has_course_repository:
            repo = self.course_repository
        else:
            repo = None

        fields = {
            'username': self.username,
            'ext_username': self.ext_username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'is_active': 1 if self.is_active else 0,
            'last_login': self.pretty_login_at,
            'last_upload_at': self.pretty_uploaded_at,
            'json_length': self.pretty_json_length,
            'github_username': self.github_username,
            'github_repo': repo,
            'comment': self.comment,
        }
        mandatory_fieldnames = ConfigSettings.users_additional_fieldnames_is_enabled_dict(current_app)
        for fieldname in mandatory_fieldnames:
            if not mandatory_fieldnames[fieldname]:
                del fields[fieldname]
        return fields

    @staticmethod
    def tidy_fieldnames(fieldnames):
        """ for a list of fieldnames, strips spaces and users underscores, etc.,
            to be as forgiving as possible with that header row
        """
        return [re.sub(r'[ -]+', '_', f.strip().lower()) for f in fieldnames]

    def get_example_data(example_user, fieldnames):
        return [ EXAMPLE_USER_DATA[example_user][fieldname] for fieldname in fieldnames ]

    def get_missing_fieldnames(fieldnames):
        additional_fields = ConfigSettings.users_additional_fieldnames(current_app)
        return [name for name in additional_fields if name not in fieldnames]

    @property
    def is_staff(self):
      return self.is_active and self.access_level in [User.TEACHING_ASSISTANT, User.ADMINISTRATOR]

    @property
    def is_administrator(self):
      return self.is_active and self.access_level == User.ADMINISTRATOR

    @property
    def is_teaching_assistant(self):
      return self.is_active and self.access_level == User.TEACHING_ASSISTANT

    @property
    def pretty_username(self):
        return self.username.title() if current_app.config[ConfigSettingNames.IS_PRETTY_USERNAME_TITLECASE.name] else self.username

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def pretty_login_at(self):
        """last logged-in timestamp or empty string."""
        if self.logged_in_at:
            return self.logged_in_at.strftime("%Y-%m-%d %H:%M")
        else:
            return ""

    @property
    def pretty_uploaded_at(self):
        """last logged-in timestamp or empty string."""
        if self.uploaded_at:
            return self.uploaded_at.strftime("%Y-%m-%d %H:%M")
        else:
            return ""

    @property
    def pretty_json_length(self):
        """pragmatic length of JSON (less than 2 is 0)"""
        if self.latest_json is not None and len(self.latest_json) > 1:
            return len(self.latest_json)
        else:
            return 0

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<User({self.username!r})>"

    def is_github_connected(self):
        """Check if the creditals for github exist and are valid"""
        return self.github_access_token is not None

    # Chached for the lifetime of the user object (so, likely only for each
    # request).
    def has_course_repository(self):
        """Check if the course repo exists for this user"""
        if not self._has_course_repository:
            # This only matches on repo name, not if it is a fork of the og repo.
            repo = self.github.get(f"/repos/{self.github_username}/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name]}").json()
            if not 'html_url' in repo:
                return False

            self._has_course_repository = True

        return True

    @property
    def course_repository(self):
        return f"https://github.com/{self.github_username}/{current_app.config[ConfigSettingNames.BUGGY_EDITOR_REPO_NAME.name]}"

    @property
    def github(self):
        if not self._github:
            self._github = Http({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f"token {self.github_access_token}",
                'User-Agent': 'Buggy Race Server'
            }, "https://api.github.com")

        return self._github
