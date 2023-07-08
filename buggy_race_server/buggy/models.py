# -*- coding: utf-8 -*-
"""Buggy model."""
import datetime as datetime

from sqlalchemy import event

from buggy_race_server.database import Column, Model, SurrogatePK, db
from buggy_race_server.user.models import User
from buggy_race_server.lib.race_specs import BuggySpecs
from buggy_race_server.utils import stringify_datetime

class Buggy(SurrogatePK, Model, BuggySpecs):
    """A buggy ready to race."""

    # set column ("varchar") max lengths here: this is useful because
    # it's actually quite fiddly to get this info back out of the model
    # when we want to truncate user's input
    STRING_COL_LENGTH = {
        "algo": 16,
        "armour": 16,
        "attack": 16,
        "aux_power_type": 16,
        "flag_color_secondary": 32,
        "flag_color": 32,
        "flag_pattern": 8,
        "power_type": 16,
        "tyres": 16,
    }

    __tablename__ = "buggies"
    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    buggy_id = Column(db.Integer(), default=1) # TODO risky default?
    qty_wheels = Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['qty_wheels']
    )
    flag_color = db.Column(
        db.String(STRING_COL_LENGTH['flag_color']),
        default=BuggySpecs.DEFAULTS['flag_color']
    )
    flag_color_secondary = db.Column(
        db.String(STRING_COL_LENGTH['flag_color_secondary']),
        default=BuggySpecs.DEFAULTS['flag_color_secondary']
    )
    flag_pattern = db.Column(
        db.String(STRING_COL_LENGTH['flag_pattern']),
        default=BuggySpecs.DEFAULTS['flag_pattern']
    )
    power_type = db.Column(
        db.String(STRING_COL_LENGTH['power_type']),
        default=BuggySpecs.DEFAULTS['power_type']
    )
    power_units = db.Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['power_units']
    )
    aux_power_type = db.Column(
        db.String(STRING_COL_LENGTH['aux_power_type']),
        default=BuggySpecs.DEFAULTS['aux_power_type']
    )
    aux_power_units = db.Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['aux_power_units']
    )
    tyres = db.Column(
        db.String(STRING_COL_LENGTH['tyres']),
        default=BuggySpecs.DEFAULTS['tyres']
    )
    qty_tyres = db.Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['qty_tyres']
    )
    armour = db.Column(
        db.String(STRING_COL_LENGTH['armour']),
        default=BuggySpecs.DEFAULTS['armour']
    )
    attack = db.Column(
        db.String(STRING_COL_LENGTH['attack']),
        default=BuggySpecs.DEFAULTS['attack']
    )
    qty_attacks = db.Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['qty_attacks']
    )
    hamster_booster = db.Column(
        db.Integer(),
        default=BuggySpecs.DEFAULTS['hamster_booster']
    )
    fireproof = db.Column(
        db.Boolean(),
        default=BuggySpecs.DEFAULTS['fireproof']
    )
    insulated = db.Column(
        db.Boolean(),
        default=BuggySpecs.DEFAULTS['insulated']
    )
    antibiotic = db.Column(
        db.Boolean(),
        default=BuggySpecs.DEFAULTS['antibiotic']
    )
    banging = db.Column(
        db.Boolean(),
        default=BuggySpecs.DEFAULTS['banging']
    )
    algo = db.Column(
        db.String(STRING_COL_LENGTH['algo']),
        default=BuggySpecs.DEFAULTS['algo']
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
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

    def get_dict(self, user):
        """ Used when creating the race file JSON """
        return {
            "username": user.username if user else None,
            "algo": self.algo,
            "antibiotic": self.antibiotic,
            "armour": self.armour,
            "attack": self.attack,
            "aux_power_type": self.aux_power_type,
            "aux_power_units": self.aux_power_units,
            "banging": self.banging,
            "buggy_id": self.buggy_id,
            "created_at": stringify_datetime(self.created_at, want_secs=False),
            "fireproof": self.fireproof,
            "flag_color_secondary": self.flag_color_secondary,
            "flag_color": self.flag_color,
            "flag_pattern": self.flag_pattern,
            "hamster_booster": self.hamster_booster,
            "id": self.id,
            "insulated": self.insulated,
            "mass": self.mass,
            "power_type": self.power_type,
            "power_units": self.power_units,
            "qty_attacks": self.qty_attacks,
            "qty_tyres": self.qty_tyres,
            "qty_wheels": self.qty_wheels,
            "total_cost": self.total_cost,
            "tyres": self.tyres,
            "user_id": self.user_id,
        }

    @staticmethod
    def get_all_buggies_with_users(want_students_only=True):
        query = db.session.query(
            Buggy, User
        ).outerjoin(User).filter(
            Buggy.user_id==User.id
        ).filter(
            User.is_active==True
        ).order_by(User.username.asc())
        if want_students_only:  
            query = query.filter(User.is_student==True)
        return query.all()

@event.listens_for(Buggy, 'before_update')
def receive_before_update(mapper, connection, target):
    target.calculate_totals()
