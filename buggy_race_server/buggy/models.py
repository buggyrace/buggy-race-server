# -*- coding: utf-8 -*-
"""Buggy model."""
import datetime as dt

from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
    reference_col,
    relationship,
)
from buggy_race_server.extensions import bcrypt

from sqlalchemy import event

class Buggy(SurrogatePK, Model):
    """A buggy ready to race."""

    POWER_TYPES = {
      "petrol":   {"cost":   4, "mass":   2, "consum": True,  "desc": "Petroleum-fuelled internal combustion engine"},
      "fusion":   {"cost": 400, "mass": 100, "consum": False, "desc": "Fusion reactor"},
      "steam":    {"cost":   3, "mass":   4, "consum": True,  "desc": "Steam engine"},
      "bio":      {"cost":   5, "mass":   2, "consum": True,  "desc": "Bio-fuelled internal combustion engine"},
      "electric": {"cost":  20, "mass":  20, "consum": True,  "desc": "Lithium-ion battery"},
      "rocket":   {"cost":  16, "mass":   2, "consum": True,  "desc": "Rocket fuel"},
      "hamster":  {"cost":   3, "mass":   1, "consum": True,  "desc": "Hamster"},
      "thermo":   {"cost": 300, "mass": 100, "consum": False, "desc": "Thermonuclear reactor"},
      "solar":    {"cost":  40, "mass":  30, "consum": False, "desc": "Bank of solar panels"},
      "wind":     {"cost":  20, "mass":  30, "consum": False, "desc": "Sailing rig"}
    }

    TYRE_TYPES = {
      "knobbly":   {"cost": 15, "mass": 20, "desc": "Great for off-roading"},
      "slick":     {"cost": 10, "mass": 14, "desc": "Fast choice for roads and rain"},
      "steelband": {"cost": 20, "mass": 28, "desc": "Slower but almost impossible to puncture"},
      "reactive":  {"cost": 40, "mass": 20, "desc": "Intelligent nanotech swarm rubber restructures itself depending on the conditions"},
      "maglev":    {"cost": 50, "mass": 30, "desc": "You can't get punctures if you don't touch the ground. Frictionless."}
    }

    ARMOUR_TYPES = {
      "none":        {"cost":   0, "mass":   0, "desc": "Unburdened and unprotected. Ideal for trips to the shops"},
      "wood":        {"cost":  40, "mass": 100, "desc": "Cheap but pragmatic (sustainable forests are used where possible)"},
      "aluminium":   {"cost": 200, "mass":  50, "desc": "Fairly strong but light"},
      "thinsteel":   {"cost": 100, "mass": 200, "desc": "Strong but heavy"},
      "thicksteel":  {"cost": 200, "mass": 400, "desc": "Very strong but very heavy"},
      "titanium":    {"cost": 290, "mass": 300, "desc": "The ultimate in plate protection, but pricey"}
    }

    ATTACK_TYPES = {
      "none":        {"cost":  0, "mass":  0, "desc": "Mostly harmless"},
      "spike":       {"cost":  5, "mass": 10, "desc": "A metal prong welded onto the superstructure"},
      "flame":       {"cost": 20, "mass": 12, "desc": "A flamethrower that puffs out a ball of fire"},
      "charge":      {"cost": 28, "mass": 25, "desc": "An electric lance like a cattleprod made of lightning"},
      "biohazard":   {"cost": 30, "mass": 10, "desc": "A cloud of infectious spores that target homonids and rodents"}
    }

    ALGO_TYPES = {
      "defensive":   {"cost": 0, "mass": 0, "desc": "Always avoids conflict: will attack but only reluctantly"},
      "steady":      {"cost": 0, "mass": 0, "desc": "The middle way: doesn't seek out attacks but makes them if opportunities present themselves"},
      "offensive":   {"cost": 0, "mass": 0, "desc": "Always seeks to attack (while attacks are available)"},
      "titfortat":   {"cost": 0, "mass": 0, "desc": "Starts steady, but petulantly switches to offence if attacked"},
      "random":      {"cost": 0, "mass": 0, "desc": "Capriciously defensive, steady, or offensive at different times during the race, based on mood"},
      "buggy":       {"cost": 0, "mass": 0, "desc": "A bad state that occurs when damaged"}
    }
    
    FLAG_PATTERNS = { 
      "plain":   {"desc": "A plain field with no secondary colour"},
      "vstripe": {"desc": "Vertical stripes"},
      "hstripe": {"desc": "Horizontal stripes"},
      "dstripe": {"desc": "Diagonal stripes"},
      "checker": {"desc": "A chequered grid"},
      "spot":    {"desc": "Spotted" }
    }

    SPECIAL_ITEMS = {
        "hamster_booster": {"cost":   5, "mass":  1, "desc": "steroids for hamsters"},
        "fireproof":       {"cost":  70, "mass":  8, "desc": "fireproof?"},
        "insulated":       {"cost": 100, "mass": 20, "desc": "insulated?"},
        "antibiotic":      {"cost":  90, "mass":  8, "desc": "antibiotic?"},
        "banging":         {"cost":  42, "mass": 40, "desc": "banging?"}
    }

    DEFAULTS = {
      'qty_wheels':           4,        # also minimum number of wheels
      'flag_color':           'white',
      'flag_color_secondary': 'black',
      'flag_pattern':         'plain',  # also single-colour rule
      'power_type':           'petrol',
      'power_units':           1,
      'aux_power_type':        None,
      'aux_power_units':       0,
      'tyres':                'knobbly',
      'qty_tyres':            4,
      'armour':               'none',
      'attack':               'none',
      'qty_attacks':          0,
      'hamster_booster':      0,
      'fireproof':            False,
      'insulated':            False,
      'antibiotic':           False,
      'banging':              False,
      'algo':                 "steady"
    }


    RULES = {
      'RACE_COST_THRESHHOLD': "buggy over cost for this race",
      'VALID_ALGO':       "unknown algorithm",
      'VALID_ARMOUR':     "unknown type of armour",
      'VALID_ATTACK':     "unknown type of attack",
      'VALID_AUX_POWER':  "unknown type of auxiliary power",
      'VALID_POWER':      "unknown type of primary power",
      'VALID_TYRES':      "unknown type of tyre",
      "VALID_PATTERN":    "unknown flag pattern",

      'MIN_WHEELS':   "must have at least {} wheels".format(DEFAULTS['qty_wheels']),
      'EVEN_WHEELS':  "must have even number of wheels",
      'FLAG_COLOURS': "flag must have two different colours if pattern is not plain",
      'ENOUGH_TYRES': "must have at least as many tyres as wheels",
      'SOFTWARE':     "must not load buggy software"
    }

    BASE_MASS_PER_WHEEL = 12

    game_data  = {
      "power_type":    POWER_TYPES,
      "tyres":         TYRE_TYPES,
      "armour":        ARMOUR_TYPES,
      "attack":        ATTACK_TYPES,
      "algo":          ALGO_TYPES,
      "flag_pattern":  FLAG_PATTERNS,
      "special":       SPECIAL_ITEMS
    }

    __tablename__ = "buggies"
    id = db.Column(db.Integer, primary_key=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    buggy_id = Column(db.Integer(), default=1) # TODO risky default?
    qty_wheels = Column(db.Integer(),
                           default=DEFAULTS['qty_wheels'])
    flag_color = db.Column(db.String(32),
                           default=DEFAULTS['flag_color'])
    flag_color_secondary = db.Column(db.String(32),
                           default=DEFAULTS['flag_color_secondary'])
    flag_pattern = db.Column(db.String(8),
                           default=DEFAULTS['flag_pattern'])
    power_type = db.Column(db.String(16),
                           default=DEFAULTS['power_type'])
    power_units = db.Column(db.Integer(),
                           default=DEFAULTS['power_units'])
    aux_power_type = db.Column(db.String(16),
                           default=DEFAULTS['aux_power_type'])
    aux_power_units = db.Column(db.Integer(),
                           default=DEFAULTS['aux_power_units'])
    tyres = db.Column(db.String(16), default=DEFAULTS['tyres'])
    qty_tyres = db.Column(db.Integer(), default=DEFAULTS['qty_tyres'])
    armour = db.Column(db.String(16), default=DEFAULTS['armour'])
    attack = db.Column(db.String(16), default=DEFAULTS['attack'])
    qty_attacks = db.Column(db.Integer(), default=DEFAULTS['qty_attacks'])
    hamster_booster = db.Column(db.Integer(), default=DEFAULTS['hamster_booster'])
    fireproof = db.Column(db.Boolean(), default=DEFAULTS['fireproof'])
    insulated = db.Column(db.Boolean(), default=DEFAULTS['insulated'])
    antibiotic = db.Column(db.Boolean(), default=DEFAULTS['antibiotic'])
    banging = db.Column(db.Boolean(), default=DEFAULTS['banging'])
    algo = db.Column(db.String(16), default=DEFAULTS['algo'])
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
        return self_qty_wheels % 2 == 0

    def __repr__(self):
        """Represent instance as a unique string."""
        return f"<Buggy({self.id!r} w:{self.qty_wheels})>"

    def calculate_totals(self):
        self.calculate_total_cost()
        self.calculate_mass()

    def calculate_total_cost(self):
        if self.qty_wheels is None:
            self.total_cost = 0
        else:
            C = 'cost'
            cost = 0
            try:
                armour_f = (100 + max(0, self.qty_wheels-Buggy.DEFAULTS['qty_wheels'])*10)/100
                cost = int(
                    Buggy.POWER_TYPES[self.power_type][C] * self.power_units
                    + Buggy.SPECIAL_ITEMS['hamster_booster'][C] * self.hamster_booster
                    + Buggy.TYRE_TYPES[self.tyres][C] * self.qty_wheels
                    + Buggy.ARMOUR_TYPES[self.armour][C] * armour_f
                    + Buggy.ATTACK_TYPES[self.attack][C] * self.qty_attacks
                  )
                if self.aux_power_type is not None:
                    cost += Buggy.POWER_TYPES[self.aux_power_type][C] * self.aux_power_units
                if self.fireproof:
                    cost += Buggy.SPECIAL_ITEMS['fireproof'][C]
                if self.insulated:
                    cost += Buggy.SPECIAL_ITEMS['insulated'][C]
                if self.antibiotic:
                    cost += Buggy.SPECIAL_ITEMS['antibiotic'][C]
                if self.banging:
                    cost += Buggy.SPECIAL_ITEMS['banging'][C]
            except (TypeError, KeyError):
                cost = None
            self.total_cost = cost

    def calculate_mass(self):
        M = 'mass'
        mass = 0
        try:
            armour_f = (100 + max(0, self.qty_wheels-Buggy.DEFAULTS['qty_wheels'])*10)/100
            mass = int(
                self.qty_wheels * Buggy.BASE_MASS_PER_WHEEL
                + Buggy.POWER_TYPES[self.power_type][M] * self.power_units
                + Buggy.SPECIAL_ITEMS['hamster_booster'][M] * self.hamster_booster
                + Buggy.TYRE_TYPES[self.tyres][M] * self.qty_tyres
                + Buggy.ARMOUR_TYPES[self.armour][M] * armour_f
                + Buggy.ATTACK_TYPES[self.attack][M] * self.qty_attacks
              )
            if self.aux_power_type is not None:
                mass += Buggy.POWER_TYPES[self.aux_power_type][M] * self.aux_power_units
            if self.fireproof:
                mass += Buggy.SPECIAL_ITEMS['fireproof'][M]
            if self.insulated:
                mass += Buggy.SPECIAL_ITEMS['insulated'][M]
            if self.antibiotic:
                mass += Buggy.SPECIAL_ITEMS['antibiotic'][M]
            if self.banging:
                mass += Buggy.SPECIAL_ITEMS['banging'][M]
        except (TypeError, KeyError):
            mass = None
        self.mass = mass

    # returns list of race rules violated (None if everything is OK)
    def get_rule_violations(self, cost_threshhold):
      violations = []
      
      if self.total_cost is not None and cost_threshhold is not None \
        and cost_threshhold > 0 and self.total_cost > cost_threshhold:
        violations.append('RACE_COST_THRESHHOLD')

      if self.algo not in Buggy.ALGO_TYPES.keys():
        violations.append('VALID_ALGO')
      if self.armour not in Buggy.ARMOUR_TYPES.keys():
        violations.append('VALID_ARMOUR')
      if self.attack not in Buggy.ATTACK_TYPES.keys():
        violations.append('VALID_ATTACK')
      if (self.aux_power_type is not None
        and self.aux_power_type not in Buggy.POWER_TYPES.keys()):
        violations.append('VALID_AUX_POWER')
      if self.power_type not in Buggy.POWER_TYPES.keys():
        violations.append('VALID_POWER')
      if self.tyres not in Buggy.TYRE_TYPES.keys():
        violations.append('VALID_TYRES')
      if self.flag_pattern not in Buggy.FLAG_PATTERNS.keys():
        violations.append('VALID_PATTERN')
      elif (self.flag_pattern != Buggy.DEFAULTS['flag_pattern'] and
        self.flag_color == self.flag_color_secondary):
        violations.append('FLAG_COLOURS')

      if self.qty_wheels is None:
        violations.append('MIN_WHEELS')
      else:
        if self.qty_wheels < Buggy.DEFAULTS['qty_wheels']:
          violations.append('MIN_WHEELS')
        elif self.qty_wheels % 2:
          violations.append('EVEN_WHEELS')
        if self.qty_tyres is None or self.qty_tyres < self.qty_wheels:
          violations.append('ENOUGH_TYRES')
      if self.algo is not None and self.algo == 'buggy': # hardcoded
        violations.append('SOFTWARE')

      if len(violations):
        return violations
      else:
        return None

@event.listens_for(Buggy, 'before_update')
def receive_before_update(mapper, connection, target):
    target.calculate_totals()
