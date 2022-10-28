# -*- coding: utf-8 -*-
"""User models."""
import datetime as datetime
from random import randint

from flask_login import UserMixin
from sqlalchemy import orm

# get the config settings (without the app context):
from buggy_race_server.config import ConfigFromEnv as config
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
    """A user of the app."""

    __tablename__ = "users"
    username = Column(db.String(80), unique=True, nullable=False)
    org_username = Column(db.String(80), unique=True, nullable=True)
    email = Column(db.String(80), unique=True, nullable=True)
    #: The hashed password
    password = Column(db.LargeBinary(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)
    buggies = db.relationship("Buggy", backref="users", lazy=True)
    latest_json = Column(db.Text(), default=False)
    github_username = Column(db.Text(), nullable=True)
    github_access_token = Column(db.Text(), nullable=True)
    is_student = Column(db.Boolean(), default=True)
    logged_in_at = Column(db.DateTime, nullable=True)
    uploaded_at = Column(db.DateTime, nullable=True)
    api_secret =  Column(db.String(30), nullable=True)
    api_secret_at = Column(db.DateTime, nullable=True)
    api_key = Column(db.String(30), nullable=True)
    notes = Column(db.Text(), default=False)

    def __init__(self, username, org_username, email, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, org_username=org_username, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

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

    def get_missing_fieldnames(fieldnames):
        required_fieldnames = ["username", "password"] + config.USERS_ADDITIONAL_FIELDNAMES
        return [name for name in required_fieldnames if name not in fieldnames]

    @property
    def is_buggy_admin(self):
      return self.username in config.ADMIN_USERNAMES_LIST

    @property
    def full_name(self):
        """Full user name."""
        return f"{self.first_name} {self.last_name}"

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
            repo = self.github.get(f"/repos/{self.github_username}/{config.BUGGY_EDITOR_REPO_NAME}").json()
            if not 'html_url' in repo:
                return False

            self._has_course_repository = True

        return True

    @property
    def course_repository(self):
        return f"https://github.com/{self.github_username}/{config.BUGGY_EDITOR_REPO_NAME}"

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
