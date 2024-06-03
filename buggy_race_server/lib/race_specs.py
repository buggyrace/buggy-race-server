from enum import Enum, auto

class RuleNames(Enum):

    def _generate_next_value_(name, start, count, last_values):
        """ ConfigSettingNames values are the same (as strings) as their names."""
        return name

    RACE_COST_THRESHOLD = auto()
    VALID_ALGO = auto()
    VALID_ARMOUR = auto()
    VALID_ATTACK = auto()
    VALID_AUX_POWER = auto()
    VALID_POWER = auto()
    VALID_TYRES = auto()
    VALID_PATTERN = auto()
    MIN_WHEELS = auto()
    EVEN_WHEELS = auto()
    FLAG_COLOURS = auto()
    ENOUGH_TYRES = auto()
    IS_POWERED = auto()
    SOFTWARE = auto()

class BuggySpecs:
    """Mixin for racing rules to be used with Buggy and RacingBuggy classes.
    Assumes fields in the buggy."""
    
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
      "wind":     {"cost":  20, "mass":  30, "consum": False, "desc": "Sailing rig"},
      "none":     {"cost":   0, "mass":   0, "consum": False, "desc": "No power"}
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
      "check":   {"desc": "A chequered grid"},
      "spot":    {"desc": "Spotted" }
    }

    SPECIAL_ITEMS = {
        "hamster_booster": {"cost":   5, "mass":  1, "desc": "steroids for hamsters"},
        "fireproof":       {"cost":  70, "mass":  8, "desc": "fireproof?"},
        "insulated":       {"cost": 100, "mass": 20, "desc": "insulated?"},
        "antibiotic":      {"cost":  90, "mass":  8, "desc": "antibiotic?"},
        "banging":         {"cost":  42, "mass": 40, "desc": "banging?"}
    }

    ATTACK_DEFENCES = {
        # presence of the defence nullifies the attack
        "flame": "fireproof",
        "charge": "insulated",
        "biohazard": "antibiotic"
    }

    DEFAULTS = {
      'qty_wheels':           4,        # also minimum number of wheels
      'flag_color':           'white',
      'flag_color_secondary': 'black',
      'flag_pattern':         'plain',  # also single-colour rule
      'power_type':           'petrol',
      'power_units':          1,
      'aux_power_type':       'none',
      'aux_power_units':      0,
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

    BASE_MASS_PER_WHEEL = 12

    GAME_DATA  = {
      "power_type":    POWER_TYPES,
      "tyres":         TYRE_TYPES,
      "armour":        ARMOUR_TYPES,
      "attack":        ATTACK_TYPES,
      "algo":          ALGO_TYPES,
      "flag_pattern":  FLAG_PATTERNS,
      "special":       SPECIAL_ITEMS
    }

    RULES = {
      RuleNames.RACE_COST_THRESHOLD.name: "buggy over cost for this race",
      RuleNames.VALID_ALGO.name:           "unknown algorithm",
      RuleNames.VALID_ARMOUR.name:         "unknown type of armour",
      RuleNames.VALID_ATTACK.name:         "unknown type of attack",
      RuleNames.VALID_AUX_POWER.name:      "unknown type of auxiliary power",
      RuleNames.VALID_POWER.name:          "unknown type of primary power",
      RuleNames.VALID_TYRES.name:          "unknown type of tyre",
      RuleNames.VALID_PATTERN.name:        "unknown flag pattern",

      RuleNames.MIN_WHEELS.name:   f"must have at least {DEFAULTS['qty_wheels']} wheels",
      RuleNames.EVEN_WHEELS.name:   "must have even number of wheels",
      RuleNames.FLAG_COLOURS.name:  "flag must have two different colours if pattern is not plain",
      RuleNames.ENOUGH_TYRES.name:  "must have at least as many tyres as wheels",
      RuleNames.IS_POWERED.name:    "primary power type must not be none",
      RuleNames.SOFTWARE.name:      "must not load buggy software"
    }

    def calculate_total_cost(self):
        if self.qty_wheels is None:
            self.total_cost = 0
        else:
            C = 'cost'
            cost = 0
            try:
                armour_f = (100 + max(0, self.qty_wheels-BuggySpecs.DEFAULTS['qty_wheels'])*10)/100
                cost = int(
                    BuggySpecs.POWER_TYPES[self.power_type][C] * self.power_units
                    + BuggySpecs.SPECIAL_ITEMS['hamster_booster'][C] * self.hamster_booster
                    + BuggySpecs.TYRE_TYPES[self.tyres][C] * self.qty_tyres
                    + BuggySpecs.ARMOUR_TYPES[self.armour][C] * armour_f
                    + BuggySpecs.ATTACK_TYPES[self.attack][C] * self.qty_attacks
                  )
                if self.aux_power_type is not None:
                    cost += BuggySpecs.POWER_TYPES[self.aux_power_type][C] * self.aux_power_units
                if self.fireproof:
                    cost += BuggySpecs.SPECIAL_ITEMS['fireproof'][C]
                if self.insulated:
                    cost += BuggySpecs.SPECIAL_ITEMS['insulated'][C]
                if self.antibiotic:
                    cost += BuggySpecs.SPECIAL_ITEMS['antibiotic'][C]
                if self.banging:
                    cost += BuggySpecs.SPECIAL_ITEMS['banging'][C]
            except (TypeError, KeyError) as e:
                cost = None
            self.total_cost = cost

    def calculate_mass(self):
        M = 'mass'
        mass = 0
        try:
            armour_f = (100 + max(0, self.qty_wheels-BuggySpecs.DEFAULTS['qty_wheels'])*10)/100
            mass = int(
                self.qty_wheels * BuggySpecs.BASE_MASS_PER_WHEEL
                + BuggySpecs.POWER_TYPES[self.power_type][M] * self.power_units
                + BuggySpecs.SPECIAL_ITEMS['hamster_booster'][M] * self.hamster_booster
                + BuggySpecs.TYRE_TYPES[self.tyres][M] * self.qty_tyres
                + BuggySpecs.ARMOUR_TYPES[self.armour][M] * armour_f
                + BuggySpecs.ATTACK_TYPES[self.attack][M] * self.qty_attacks
              )
            if self.aux_power_type is not None:
                mass += BuggySpecs.POWER_TYPES[self.aux_power_type][M] * self.aux_power_units
            if self.fireproof:
                mass += BuggySpecs.SPECIAL_ITEMS['fireproof'][M]
            if self.insulated:
                mass += BuggySpecs.SPECIAL_ITEMS['insulated'][M]
            if self.antibiotic:
                mass += BuggySpecs.SPECIAL_ITEMS['antibiotic'][M]
            if self.banging:
                mass += BuggySpecs.SPECIAL_ITEMS['banging'][M]
        except (TypeError, KeyError) as e:
            mass = None
        self.mass = mass

    # returns list of race rules violated (empty if everything is OK)
    def get_rule_violations(self, cost_limit):
        if cost_limit is None:
            raise ValueError("missing cost limit for race")

        violations = []

        if self.total_cost is None:
            raise ValueError(f"buggy ({self.id or self.username }) is missing total_cost")
            
        if cost_limit > 0 and self.total_cost > cost_limit:
            violations.append(RuleNames.RACE_COST_THRESHOLD.name)

        if self.algo not in BuggySpecs.ALGO_TYPES.keys():
            violations.append(RuleNames.VALID_ALGO.name)
        if self.armour not in BuggySpecs.ARMOUR_TYPES.keys():
            violations.append(RuleNames.VALID_ARMOUR.name)
        if self.attack not in BuggySpecs.ATTACK_TYPES.keys():
            violations.append(RuleNames.VALID_ATTACK.name)
        if self.power_type not in BuggySpecs.POWER_TYPES.keys():
            violations.append(RuleNames.VALID_POWER.name)
        elif self.power_type == 'none': # hardcoded
            violations.append(RuleNames.IS_POWERED.name)
        if self.aux_power_type not in BuggySpecs.POWER_TYPES.keys():
            violations.append(RuleNames.VALID_AUX_POWER.name)
        if self.tyres not in BuggySpecs.TYRE_TYPES.keys():
            violations.append(RuleNames.VALID_TYRES.name)
        if self.flag_pattern not in BuggySpecs.FLAG_PATTERNS.keys():
            violations.append(RuleNames.VALID_PATTERN.name)
        elif (self.flag_pattern != BuggySpecs.DEFAULTS['flag_pattern'] and
            self.flag_color == self.flag_color_secondary):
            violations.append(RuleNames.FLAG_COLOURS.name)
        if (self.qty_wheels is None or
            self.qty_wheels < BuggySpecs.DEFAULTS['qty_wheels']):
            violations.append(RuleNames.MIN_WHEELS.name)
        elif self.qty_wheels % 2:
            violations.append(RuleNames.EVEN_WHEELS.name)
        if self.qty_tyres is None or self.qty_tyres < self.qty_wheels:
            violations.append(RuleNames.ENOUGH_TYRES.name)
        if self.algo is not None and self.algo == 'buggy': # hardcoded
            violations.append(RuleNames.SOFTWARE.name)

        return violations
