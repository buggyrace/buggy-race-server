# -*- coding: utf-8 -*-
"""Buggy model."""

from datetime import datetime

from buggy_race_server.database import Column, Model, SurrogatePK, db


class Announcement(SurrogatePK, Model):
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
