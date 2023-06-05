# -*- coding: utf-8 -*-
"""Buggy model."""
import datetime as datetime

from sqlalchemy import event

from buggy_race_server.database import Column, Model, SurrogatePK, db
from buggy_race_server.user.models import User
from buggy_race_server.lib.race_specs import BuggySpecs


class Buggy(SurrogatePK, Model, BuggySpecs):
    """A buggy ready to race."""

    __tablename__ = "buggies"
    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    buggy_id = Column(db.Integer(), default=1) # TODO risky default?
    qty_wheels = Column(db.Integer(),
                           default=BuggySpecs.DEFAULTS['qty_wheels'])
    flag_color = db.Column(db.String(32),
                           default=BuggySpecs.DEFAULTS['flag_color'])
    flag_color_secondary = db.Column(db.String(32),
                           default=BuggySpecs.DEFAULTS['flag_color_secondary'])
    flag_pattern = db.Column(db.String(8),
                           default=BuggySpecs.DEFAULTS['flag_pattern'])
    power_type = db.Column(db.String(16),
                           default=BuggySpecs.DEFAULTS['power_type'])
    power_units = db.Column(db.Integer(),
                           default=BuggySpecs.DEFAULTS['power_units'])
    aux_power_type = db.Column(db.String(16),
                           default=BuggySpecs.DEFAULTS['aux_power_type'])
    aux_power_units = db.Column(db.Integer(),
                           default=BuggySpecs.DEFAULTS['aux_power_units'])
    tyres = db.Column(db.String(16), default=BuggySpecs.DEFAULTS['tyres'])
    qty_tyres = db.Column(db.Integer(), default=BuggySpecs.DEFAULTS['qty_tyres'])
    armour = db.Column(db.String(16), default=BuggySpecs.DEFAULTS['armour'])
    attack = db.Column(db.String(16), default=BuggySpecs.DEFAULTS['attack'])
    qty_attacks = db.Column(db.Integer(), default=BuggySpecs.DEFAULTS['qty_attacks'])
    hamster_booster = db.Column(db.Integer(), default=BuggySpecs.DEFAULTS['hamster_booster'])
    fireproof = db.Column(db.Boolean(), default=BuggySpecs.DEFAULTS['fireproof'])
    insulated = db.Column(db.Boolean(), default=BuggySpecs.DEFAULTS['insulated'])
    antibiotic = db.Column(db.Boolean(), default=BuggySpecs.DEFAULTS['antibiotic'])
    banging = db.Column(db.Boolean(), default=BuggySpecs.DEFAULTS['banging'])
    algo = db.Column(db.String(16), default=BuggySpecs.DEFAULTS['algo'])
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_cost = db.Column(db.Integer(), default=0)
    mass = db.Column(db.Integer(), default=0)

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
        self.calculate_totals()

    @property
    def is_even_number_of_wheels(self):
        """Tests if wheels are even."""
        return self.qty_wheels % 2 == 0

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Buggy({self.id!r} w:{self.qty_wheels})>"

    def calculate_totals(self):
        self.calculate_total_cost()
        self.calculate_mass()


    @staticmethod
    def get_all_buggies_with_usernames(want_inactive_users=False, want_students_only=True):
        # TODO shockingly building my own join because somehow the SQLAlchemy
        # TODO relationship isn't putting User into the buggy. Don't look
        # TODO Used db.session with .joins and everything. Sigh.
        users_by_id = dict()
        if want_inactive_users:
           print("* not implemented — buggies only for active users")
        if want_students_only:
            users = User.query.filter_by(is_active=True, is_student=True).all()
        else:
            users = User.query.filter_by(is_active=True).all()
        for user in users:
            users_by_id[user.id] = user
        buggies = Buggy.query.all()
        for b in buggies:
          if user := users_by_id.get(b.user_id):
            b.username = user.username
            b.pretty_username = user.pretty_username
        return buggies

@event.listens_for(Buggy, 'before_update')
def receive_before_update(mapper, connection, target):
    target.calculate_totals()
