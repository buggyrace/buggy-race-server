# run buggy race
#================

# Does not require access to database, etc: just the race_specs.py
# from buggy_race_server.lib (for the shared specifications)

# Doing it this way for now so no load on production server
# and can run as many times here as wanted
#
# Before you start:
#   * Download a race file from the race server
#      - it might also include buggies that are entered into the race
#   * if there aren't buggies in the race file (or you don't want to use them)
#      * Download the a buggy CSV file from the race server
#
# When you've finished:
#
#   * on race server: admin → races → [select race] → upload results
#   * check the warnings (if any) are acceptable
#   * if there were warnings, either:
#      * edit the JSON to fix them
#      * upload again, this time with "ignore warnings"
#
# See the docs on uploading race results:
# https://www.buggyrace.net/docs/races/uploading-results.html
#
#------------------------------------------------------------------------------

import os
import optparse
import sys
import csv
import json
import math
import re
from datetime import datetime, timezone # will need locale really
from random import randint, shuffle
from enum import Enum
from time import sleep

sys.path.append(os.path.join(os.path.dirname(__file__), '..', ''))
from buggy_race_server.lib.race_specs import BuggySpecs

parser = optparse.OptionParser()
parser.add_option(
    "-c", "--csv", dest="is_using_buggies_csv", action="store_true",
    help="load the buggies from a CSV file (if you've got a JSON race file, "
         "you can still use it, but this option ignores any buggies in that "
         "JSON and loads them from the CSV file instead)"
)
parser.add_option(
    "-n", "--no-race-file", dest="no_race_file", action="store_true",
    help="run a race without loading data from a race file (normally you don't "
         "want to do this because you've downloaded a race file from your race"
         "server)"
)
opts, args = parser.parse_args()

# opts.no_race_file

DEFAULT_RACE_FILENAME_JSON = 'race.json'
DEFAULT_CSV_FILENAME = 'buggies.csv'
DEFAULT_RACE_FILENAME = 'race.log'
DEFAULT_RESULTS_FILENAME = 'race-results.json'

# these defaults are only used if there's no race file:
# (because if there is a race file, it should contain all this information,
# and deviating from it will (at least) generate warnings when you upload the
# results and (at worst) create a race that doesn't match the declared race
# -- in particular, changing cost limit or lap length from what's up on the
# race server is going to get you into trouble
DEFAULT_COST_LIMIT = 250
DEFAULT_INITIAL_STEPS = 100
DEFAULT_MORE_STEPS =  50
DEFAULT_MAX_LAPS = 2
DEFAULT_LAP_LENGTH = 464
DEFAULT_IS_DNF_A_POSITION = True

DEFAULT_REPAIR_DICE = "2d3"
DEFAULT_ATTACK_RANGE = 2
DEFAULT_PK_OF_KARMIC_INJURY = 42

DEFAULT_PUNCTURE_MULTIPLIER = 1

DEFAULT_PK_OF_PUNCTURE = {
    "knobbly":   3 * DEFAULT_PUNCTURE_MULTIPLIER,
    "slick":     6 * DEFAULT_PUNCTURE_MULTIPLIER,
    "steelband": 2 * DEFAULT_PUNCTURE_MULTIPLIER,
    "reactive":  1 * DEFAULT_PUNCTURE_MULTIPLIER,
    "maglev":    0
}

POSITIONS = {
    1: "FIRST PLACE",
    2: "nd",
    3: "rd",
    4: "th",
    5: "th",
}

# later... F=ma, but for now, just move like Ludo
POWER_DATA = {
    "bio": {
      "delta": "3d6",
      "rate": 0.2,
    }, 
    "electric": {
      "delta": "3d4",
      "rate": 0.06,
    }, 
    "fusion": {
      "delta": "3d6",
      "rate": 0,
    }, 
    "hamster": {
      "delta": "1d6+2",
      "rate": 0.3,
    }, 
    "none": {
      "delta": "0d6",
      "rate": 0,
    }, 
    "petrol": {
      "delta": "3d6+2",
      "rate": 0.2,
    }, 
    "rocket": {
      "delta": "8d6",
      "rate": 1,
    }, 
    "solar": {
      "delta": "1d8",
      "rate": 0,
    }, 
    "steam": {
      "delta": "3d4",
      "rate": 0.2,
    }, 
    "thermo": {
      "delta": "5d6",
      "rate": 0,
    }, 
    "wind": {
      "delta": "1d10",
      "rate": 0,
    }
}

DICE_STR_RE = re.compile(r"(\d+)d(\d+)\+?(\d+)?")
def score_from_dice(dstring):
    if m := re.match(DICE_STR_RE, dstring):
        qty = int(m.group(1))
        sides = int(m.group(2))
        total = int(m.group(3)) if m.group(3) else 0
        for i in range(qty):
            total += randint(1, sides)
        return total
    else:
        return 0

def get_pretty_position(n):
    if n == 1:
        return "FIRST PLACE"
    elif n == 2:
        return "SECOND PLACE"
    elif n == 3:
        return "THIRD PLACE"
    if n in [11, 12, 13]:
        suffix = "th"
    else:
        last_digit = n % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"
    return f"{n}{suffix} place"

class EventType(Enum):
    ATTACK_BIOHAZARD = "ab"
    ATTACK_CHARGE = "ac"
    ATTACK_FLAME = "af"
    ATTACK_SPIKE = "as"
    CHASSIS_FAIL = "xc"
    FINISH = "f"
    MESSAGE = "s" # actually "String message"
    PUNCTURE = "p"

EVENT_BY_ATTACK = {
    "biohazard": EventType.ATTACK_BIOHAZARD,
    "charge": EventType.ATTACK_CHARGE,
    "flame": EventType.ATTACK_FLAME,
    "spike": EventType.ATTACK_SPIKE
}

PK_SPIKE_VS_ARMOUR = {
    "none":       950,
    "wood":       800,
    "aluminium":  600,
    "thinsteel":  400,
    "thicksteel": 200,
    "titanium":   100,
}

PK_DECIDE_TO_ATTACK = {
    "defensive": 100,
    "steady":    300,
    "offensive": 800,
    "titfortat":   0,
    "random":    500,
    "buggy":       0
}

def pk(prob): # probability in 1000
    return randint(0, 1000) < prob


class RacingBuggy(BuggySpecs):

    NO_RACE_POSITION = -1

    ATTRIB_TYPES = {
        "algo": str,
        "antibiotic": bool,
        "armour": str,
        "attack": str,
        "aux_power_type": str,
        "aux_power_units": int,
        "banging": bool,
        "buggy_id": int,
        "created_at": str, # datetime
        "fireproof": bool,
        "flag_color_secondary": str,
        "flag_color": str,
        "flag_pattern": str,
        "hamster_booster": int,
        "id": int,
        "insulated": bool,
        "mass": int,
        "power_type": str,
        "power_units": int,
        "qty_attacks": int,
        "qty_tyres": int,
        "qty_wheels": int,
        "total_cost": int,
        "tyres": str,
        "user_id": int,
        "username": str,
    }

    def __init__(self, buggy_data):
        for i, k in enumerate(buggy_data.keys()):
            if k in RacingBuggy.ATTRIB_TYPES:
                attr_type = RacingBuggy.ATTRIB_TYPES[k] # e.g., str, int, bool
                if attr_type == str: # check value is a member
                    kk = "power_type" if k == "aux_power_type" else k
                    if kk in RacingBuggy.GAME_DATA: # do we have members?
                        if buggy_data[k] not in RacingBuggy.GAME_DATA[kk]:
                            buggy_data[k] = RacingBuggy.DEFAULTS[k]
                try: # to cast the value to the expected type...
                    self.__setattr__(k, attr_type(buggy_data[k])) 
                except ValueError: # missing value (or wrong format?)
                    default = RacingBuggy.DEFAULTS.get(k)
                    if default is None:
                        self.__setattr__(k, attr_type()) # empty default
                    else:
                      self.__setattr__(k, attr_type(default))
            else:
                pass # debug: f"[!] key {k} not in attrib types — ignoring ({i})"
        for k in RacingBuggy.ATTRIB_TYPES:
            if k not in vars(self):
                # unexpected, because we're checking that every column in present
                # when we load CSV: this is belt-and-braces 
                raise ValueError(f"column/key \"{k}\" is missing from buggy {i}")
        self.data = buggy_data
        self.position = RacingBuggy.NO_RACE_POSITION
        self.qty_good_wheels = self.qty_wheels
        self.d = 0   # distance from start
        self.a = 0   # acceleration
        self.s = 0   # speed
        self.is_on_aux = False
        self.is_parked = False
        self.violations = None
        self.nom = "[" + self.username + "]"
        # TODO maybe report if the calculations yield different results
        #      from the values stored in the CSV?
        self.calculate_total_cost()
        self.calculate_mass()
        self.damage_percent = 0

    def __str__(self):
        return f"[{self.username}]"

    def result_data(self):
        """Data for each buggy that is presented in the `results` section of
        the JSON that is uploaded to the server."""

        return {
            "username": self.username,
            "user_id": self.user_id,
            "flag_color": self.flag_color,
            "flag_color_secondary": self.flag_color_secondary,
            "flag_pattern": self.flag_pattern,
            "cost": self.total_cost,
            "race_position": self.position,
            "violations_str": ",".join(self.violations)
        }

    def power_in_use(self):
        if self.is_parked:
            return None
        elif self.is_on_aux:
            return None if self.aux_power_type == "none" else self.aux_power_type
        else:
            return self.power_type

    def advance(self, power_in_use):
        if not self.qty_wheels:
            return
        good_wheel_ratio = self.qty_good_wheels / self.qty_wheels
        dstring = POWER_DATA[power_in_use]["delta"]
        delta = score_from_dice(dstring)
        delta *= good_wheel_ratio
        if pk(100 * self.damage_percent):
            delta = int(delta / ( 1 + score_from_dice("1d2")/2 ) )
        self.d += math.ceil(delta)

    def consume_power(self):
        pwr = self.power_in_use()
        msg = None
        if pwr is not None:
            if BuggySpecs.POWER_TYPES[pwr]['consum']:
                if self.power_units > 0:
                    # have not run out of power
                    self.power_units -= POWER_DATA[pwr]['rate'] * (randint(0, 10)/50)
                    self.advance(pwr)
                    if pwr == "hamster" and self.hamster_booster > 0 and pk(300):
                        self.d += score_from_dice("1d6+10")
                        self.hamster_booster -= 1
                        msg = f"employs hamster boost ({self.hamster_booster} left)"
                    # TODO reduced mass
                else: # have run out of power
                    self.power_units = 0
                    if self.is_on_aux: # no auxiliary power left, race over for this one
                        if not self.is_parked:
                            msg = "is out of auxillary power"
                        self.is_parked = True
                    elif self.aux_power_type == "none": # didn't pack any auxilliary
                        if not self.is_parked:
                            msg = "is out of power (and has no auxillary power)"
                        self.is_parked = True
                    else:
                        self.power_units = self.aux_power_units
                        self.is_on_aux = True
                        msg = f"is out of {pwr} power so switches to auxillary ({self.aux_power_type})"
            else: # non-consumable power source
                if self.power_units > 0:
                    self.advance(pwr)
                else:
                    self.power_units = 0
                    if self.is_on_aux: # no auxiliary power left, race over for this one
                        if not self.is_parked:
                            msg = "is out of auxillary power"
                        self.is_parked = True
                    elif self.aux_power_type == "none": # didn't pack any auxilliary
                        if not self.is_parked:
                            msg = "is out of power (and has no auxillary power)"
                        self.is_parked = True
        else:
            pass # power is none
        return msg

    def suffer_puncture(self):
        self.qty_tyres -= 1
        if self.qty_tyres < self.qty_good_wheels:
            self.qty_good_wheels = self.qty_tyres
        if self.qty_tyres == 0:
            self.is_parked = True

    def suffer_attack(self, attack):
        # if attack == "biohazard":
        #     # hamsters are the only motive power compromised by bio
        #     if self.power_type == "hamster" and self.power_units > 0:
        #         qty_hamsters_lost = min(self.power_units, score_from_dice("2d4"))
        #         self.power_units = self.power_units - qty_hamsters_lost
        #     elif self.aux_power_type == "hamster" and self.aux_power_units > 0:
        #         qty_hamsters_lost = min(self.aux_power_units, score_from_dice("2d4"))
        #         self.aux_power_units = self.aux_power_units - qty_hamsters_lost
        self.damage_percent += score_from_dice("3d6")
        if self.damage_percent >= 100:
            self.is_parked = True

    def set_rule_violations(self, cost_limit):
        self.violations = self.get_rule_violations(cost_limit)

    @staticmethod
    def get_json_list_of_buggies(buggies):
        return [buggy.result_data()
            for buggy in sorted(
                buggies,
                key=lambda buggy: (buggy.position, buggy.total_cost, buggy.username)
            )
        ]

class RaceEvent():
    def __init__(self, buggy=None, delta=None, event_type=None, msg=None):
        self.buggy = buggy if buggy else None
        # if delta is not None and not f"{delta}".isnumeric():
        #     raise ValueError(f"delta is not number ({delta})")
        self.delta = delta
        if event_type is not None and type(event_type) is not EventType:
            raise ValueError(f"event_type is not valid ({event_type})")
        self.event_type = event_type.value if event_type else None
        self.string = msg # it's 's' for string, not 'm' for message
    
    def to_json(self):
        spacer = " " * 8
        sparse_dict = {}
        if self.buggy is not None: sparse_dict["b"] = self.buggy.username
        if self.delta is not None: sparse_dict["d"] = self.delta
        if self.event_type is not None: sparse_dict["e"] = self.event_type
        if self.string is not None: sparse_dict["s"] = self.string
        return spacer + json.dumps(sparse_dict, indent=2).replace("\n", "\n"+spacer)

    def to_dict(self):
        sparse_dict = {}
        if self.buggy is not None: sparse_dict["b"] = self.buggy.username
        if self.delta is not None: sparse_dict["d"] = self.delta
        if self.event_type is not None: sparse_dict["e"] = self.event_type
        if self.string is not None: sparse_dict["s"] = self.string
        return sparse_dict

    @staticmethod
    def get_list_of_events(list_of_events):
        return [
            event.to_dict() for event in list_of_events
        ]

# ---------------------------------------------------------------------

def load_race_file(json_filename=None):
    race_data = {}
    if not json_filename:
        json_filename = str(input(f"[?] Filename of buggy race data in JSON: [{DEFAULT_RACE_FILENAME_JSON}] ")).strip()
    if json_filename == "":
        print(f"[ ] defaulting to {DEFAULT_RACE_FILENAME_JSON}")
        json_filename = DEFAULT_RACE_FILENAME_JSON
    if not os.path.isfile(json_filename):
        raise FileNotFoundError(f"can't find JSON file containing race data (\"{json_filename}\") ")
    try:
        with open(json_filename, "r") as read_file:
            race_data = json.load(read_file)
    except UnicodeDecodeError as e:
        print("[!] Encoding error (maybe that wasn't a good JSON file?)")
        quit()
    except json.decoder.JSONDecodeError as e:
        print("[!] Failed to parse JSON data:\n    {e}")
        quit()
    title_str = f"Race {race_data.get('title')}" # TODO
    print(f"\n[ ] {title_str}")
    print(f"[ ] {'=' * len(title_str)}\n")
    buggy_data = race_data.get("buggies")
    race_data["buggies"] = []
    if buggy_data is not None:
        if opts.is_using_buggies_csv:
            print("[ ] ignoring buggies in race file, because --csv option")
        else:
            print("[ ] Processing buggies: ", end="")
            for i, buggy_data in enumerate(buggy_data):
                for k in BuggySpecs.DEFAULTS:
                    if k not in buggy_data:
                        raise ValueError(f"column/key \"{k}\" is missing from CSV (buggy {i})")
                    if buggy_data[k] == '': # anomaly of CSV dumping: tidy nones
                        buggy_data[k] = None
                    if type(BuggySpecs.DEFAULTS[k]) == bool:
                        if type(buggy_data[k]) != bool:
                            buggy_data[k] = buggy_data[k].lower() == "true"
                race_data["buggies"].append(RacingBuggy(buggy_data))
                print(".", end="", flush=True)
            print("OK", flush=True)
    return race_data

def load_csv(csv_filename=None):
    if csv_filename is None or csv_filename == '':
        csv_filename = str(input(f"[?] Filename of buggy data in CSV: [{DEFAULT_CSV_FILENAME}] ")).strip()
    if csv_filename == "":
        print(f"[ ] defaulting to {DEFAULT_CSV_FILENAME}")
        csv_filename = DEFAULT_CSV_FILENAME
    if not os.path.isfile(csv_filename):
        raise FileNotFoundError(f"can't find CSV file containing buggy data (\"{csv_filename}\") ")
    print("[ ] reading CSV...")
    with open(csv_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        headers = []
        buggy_data = []
        for row in reader:
            # print(row)
            buggy_data.append(row)
            # if len(headers):
            #     buggy_data.append(row)
            # else:
            #     headers = row.keys()
        print(f"[+] read data for {len(buggy_data)} buggies")
    buggies = []
    print("[ ] Processing: ", end="")
    for i, buggy_data in enumerate(buggy_data):
        for k in BuggySpecs.DEFAULTS:
            if k not in buggy_data:
               raise ValueError(f"column/key \"{k}\" is missing from CSV (buggy {i})")
            if buggy_data[k] == '': # anomaly of CSV dumping: tidy nones
                buggy_data[k] = None
            if type(BuggySpecs.DEFAULTS[k]) == bool:
                # print(f"{} is boolean! ({})".format(k, b[k]))
                buggy_data[k] = buggy_data[k].lower() == "true"
        buggies.append(RacingBuggy(buggy_data))
        print(".", end="", flush=True)
    print(" OK")
    return buggies

def report_puncture(racelog, buggy, type="puncture"):
    if buggy.qty_good_wheels == 0:
        punc_str = "no tyres left: parked"
    else:
        punc_str = "use spare: still" if buggy.qty_good_wheels == buggy.qty_wheels else "now"
        punc_str += f" running on {buggy.qty_good_wheels} of {buggy.qty_wheels} wheels"
    racelog(
        buggy=buggy,
        event_type=EventType.PUNCTURE,
        msg=f"{type}! {punc_str}"
    )

def input_integer(name, minimum=1, default=-1, prompt=None):
    if prompt is None:
        prompt = f"{name.title()}?"
    ret_val = minimum - 1
    while ret_val < minimum:
        ret_val = input(f"[?] {prompt} [{default}] ").strip()
        if ret_val == '':
            ret_val = default
        else:
            try:
                ret_val = int(ret_val)
                if ret_val < minimum:
                    print(f"[!] too small: minimum is {minimum}")
            except ValueError:
                print("[!] oops! Wasn't an integer. Try again...")
                ret_val = minimum - 1
    print(f"[ ] {name}: {ret_val}")
    return ret_val    

def input_boolean(name, default=True, prompt=None):
    if prompt is None:
        prompt = f"{name.title()}?"
    pretty_default = "y" if default else "n"
    ret_val = input(f"[?] {prompt} [{pretty_default}] ").strip()
    ret_val = default if not ret_val else ret_val.lower().startswith("y")
    print(f"[ ] {name} {ret_val}")
    return ret_val

def run_race(race_data):
    buggies_entered = race_data["buggies"]
    events = [] # into here goes one array for each step
    events_this_step = []
    next_finisher_position = 1
    finishers_this_step = 0

    def racelog(**kwargs):
        ev = RaceEvent(**kwargs)
        #text = f"{steps:=5} {ev.buggy_id:12s} {ev.string}"
        buggy_id = ev.buggy.username if buggy else ""
        show_delta = f"delta: {ev.delta}" if ev.delta else ""
        print(f"[.] {steps:=5} [{buggy_id}] {show_delta} {ev.string or ''}", flush=True)
        events_this_step.append(ev)

    print(f"[ ] buggies entered for this race: {len(buggies_entered)}")

    cost_limit = input_integer(
        "cost limit",
        minimum=10,
        default=race_data.get("cost_limit") or DEFAULT_COST_LIMIT, 
        prompt="Maximum buggy cost for this race?"
    )
    max_laps = input_integer(
        "number of laps",
        minimum=1,
        default=race_data.get("max_laps") or DEFAULT_MAX_LAPS,
        prompt="Number of laps for this race?"
    )
    svg_path_length = input_integer(
        "SVG path length",
        minimum=1,
        default=race_data.get("svg_path_length") or race_data.get("svg_path_length") or DEFAULT_LAP_LENGTH,
    )
    lap_length = input_integer(
        "lap length",
        minimum=1,
        default=race_data.get("lap_length") or race_data.get("svg_path_length") or DEFAULT_LAP_LENGTH,
    )
    dnf_default = race_data.get("is_dnf_position") 
    if dnf_default is None:
        print("[!] !!! caution: \"is DNF a position?\" is not in the race file: ")
        print("[!]     maybe check what's up on the server for this race")
        dnf_default = DEFAULT_IS_DNF_A_POSITION
    is_dnf_a_position = input_boolean(
        "is DNF position?",
        default=dnf_default,
        prompt="Is Did-Not-Finish (DNF) a position?"
    )
    pretty_race_length = f"{max_laps} lap race"
    race_start_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print("[ ] Scrutineering: checking race rules...")
    qty_violators = 0
    buggies = []

    for buggy in buggies_entered:
        try:
            buggy.set_rule_violations(cost_limit)
        except ValueError as e:
            print(f"[!] cost problem: {e}")
            continue
        if buggy.violations:
            qty_violators += 1
            print(f"[ ]    {buggy.nom} {buggy.qty_wheels}×o ({buggy.qty_tyres}) {buggy.flag_color} cost={buggy.total_cost}")
            print(f"[-]        violates: {'+'.join(buggy.violations)}")
        else:
            buggy.position = 0
            buggies.append(buggy)
    print(f"[*] {qty_violators} buggies are excluded due to race rule violations")
    print(f"[ ] next: {len(buggies)} buggies ready to start the race:")
    print("[ ]       " + ", ".join([b.username for b in buggies]))
    finishers = []
    non_finishers = []
    if len(buggies) == 0:
        print("[!] look like this race may need to be abandoned because nobody entered it")
    else:
        if not (
            input_boolean(
                "ok to start?",
                default=True,
                prompt="Check this ↑ all looked good... OK to start race?"
            )
        ):
            print("[ ] cancelled race")
            exit()
        steps = 0
        max_steps = DEFAULT_INITIAL_STEPS 
        qty_attacks_launched = 0
        while steps < max_steps:
            events_this_step = []
            next_finisher_position += finishers_this_step # 2 buggies tie, next one is 3rd
            finishers_this_step = 0
            steps += 1
            print(f"------------------------ step {steps} ------------------------")

            if steps > 2: # no fighting on the start line, it's unsporting
                # calculate attacks:
                # doing this before anyone has moved: now we calculate
                # proximity (caculating attacks during the move loop is unfair
                # on buggies early/late in the move cycle)
                # TODO randomise the order of the buggies to prevent advantage
                # to earlier (because a parked buggy won't attack so the order
                # of attack matters )
                shuffle(buggies)
                for buggy in [b for b in buggies if b.qty_attacks > 0 and not b.is_parked]:
                    if buggy.attack is None or buggy.attack == 'none':
                        continue
                    attack_range = DEFAULT_ATTACK_RANGE
                    targets = []
                    for target in buggies:
                        proximity = abs(target.d - buggy.d)
                        if target != buggy and proximity <= attack_range:
                            targets.append(target)
                    if targets:
                        shuffle(targets)
                        target = targets[0]
                        proximity = abs(target.d - buggy.d)
                        racelog(
                            buggy=buggy,
                            event_type=EVENT_BY_ATTACK[buggy.attack],
                            msg=f"attacks {target} with {buggy.attack}"
                        )
                        if buggy.attack == "spike":
                            pretty_armour = ""
                            if target.armour != "none":
                                pretty_armour = f" through {target.armour}"
                            if pk(PK_SPIKE_VS_ARMOUR[target.armour]):
                                if pk(target.qty_good_wheels * 100) and pk(100 * DEFAULT_PK_OF_PUNCTURE[target.tyres]) :
                                    target.suffer_puncture()
                                    report_puncture(racelog, target, f"spike puncture{pretty_armour}")
                                else:
                                    target.suffer_attack(buggy.attack)
                                    racelog(
                                        buggy=target,
                                        event_type=EventType.MESSAGE,
                                        msg=f"now at {target.damage_percent}% damage"
                                    )
                            else:
                                if target.armour != "none":
                                    pretty_armour = f"{target.armour} "
                                racelog(
                                    buggy=target,
                                    event_type=EventType.MESSAGE,
                                    msg=f"{pretty_armour} repels {buggy}'s attack"
                                )
                        else: # buggy attack is not-spike
                            if pk(DEFAULT_PK_OF_KARMIC_INJURY):
                                buggy.suffer_attack(buggy.attack)
                                racelog(
                                    buggy=buggy,
                                    event_type=EventType.MESSAGE,
                                    msg=f"suffers karmic self-injury: now {buggy.damage_percent}% damage"
                                )
                            else:
                                defence = BuggySpecs.ATTACK_DEFENCES.get(buggy.attack)
                                if getattr(target, defence):
                                    racelog(
                                        buggy=target,
                                        event_type=EventType.MESSAGE,
                                        msg=f"{defence}: immune to {buggy}'s {buggy.attack}"
                                    )
                                else:
                                    target.suffer_attack(buggy.attack)
                                    racelog(
                                        buggy=target,
                                        event_type=EventType.MESSAGE,
                                        msg=f"now at {target.damage_percent}% damage"
                                    )
                        buggy.qty_attacks -= 1
                        qty_attacks_launched += 1
                        if buggy.qty_attacks == 0:
                            racelog(
                                buggy=buggy,
                                event_type=EventType.MESSAGE,
                                msg="has no attacks left"
                            )
                        if target.algo == "titfortat":
                            target.algo == "offensive"
                            racelog(
                                buggy=target,
                                event_type=EventType.MESSAGE,
                                msg="titfortat algo switched to offensive"
                            )

            qty_active = 0
            for buggy in buggies:
                if buggy.damage_percent > 0:
                    buggy.damage_percent = max(0, buggy.damage_percent - score_from_dice(DEFAULT_REPAIR_DICE))
                    if buggy.damage_percent == 0:
                        racelog(
                            buggy=buggy,
                            event_type=EventType.MESSAGE,
                            msg="all damage repaired"
                        )
                if not buggy.is_parked:
                    delta = 0
                    qty_active += 1
                    if pk(1) and pk(buggy.mass/buggy.qty_wheels):
                        racelog(
                            buggy=buggy,
                            event_type=EventType.CHASSIS_FAIL,
                            msg="catastrophic chassis failure: buggy breaks."
                        )
                        buggy.is_parked = True
                    else:
                        power = buggy.power_in_use()
                        if power is not None:
                            distance_before = buggy.d
                            if msg := buggy.consume_power():
                                racelog(buggy=buggy, msg=msg)
                            delta = buggy.d - distance_before
                            if (delta):
                                racelog(buggy=buggy, delta=delta)
                            # else: print(f"[ ] {buggy.username} does not move")
                        else:
                            racelog(
                                buggy=buggy,
                                msg=f"ran out of {power} power"
                            )
                    if delta and pk(DEFAULT_PK_OF_PUNCTURE[buggy.tyres] * buggy.qty_good_wheels):
                        buggy.suffer_puncture()
                        report_puncture(racelog, buggy)
                        #   ? risk of primary power fail?
                    if max_laps and buggy.d // lap_length >= max_laps:
                        buggy.is_parked = True
                        finishers_this_step += 1
                        buggy.position = next_finisher_position
                        position_str = get_pretty_position(next_finisher_position)
                        finishers.append(buggy)
                        if finishers_this_step > 1:
                            position_str = f"tied {position_str}"
                        racelog(
                            buggy=buggy,
                            event_type=EventType.FINISH,
                            msg=f"crosses the finish line in {position_str} ({pretty_race_length})"
                        )
                        buggy.d += 4 + score_from_dice("1d4") # nudge over line
                else:
                    pass # buggy is parked

            if qty_active == 0:
                print("[ ] no buggies moving...")
                break
            else:
                if steps == max_steps:
                    more_steps = str(
                    input(f"[?] {steps} steps so far: add more? [+{DEFAULT_MORE_STEPS}] ")).strip()
                    if more_steps == '':
                        more_steps = DEFAULT_MORE_STEPS
                    else:
                        try:
                            more_steps = int(more_steps)
                        except ValueError:
                            print("[!] integer greater than 1 needed")
                        more_steps = 0
                    if more_steps > 0:
                        print(f"[+] running race for another +{more_steps} steps")
                    else:
                        print("[-] no more steps, time is up")
                    max_steps += more_steps
            events.append(events_this_step)
        print(f"[ ] attacks launched in that race: {qty_attacks_launched}")
        print(f"[:] race ends after {steps} steps")
        non_finishers = sorted(
            [buggy for buggy in buggies if buggy.position == 0 ],
            key=lambda buggy: buggy.d,
            reverse=True
        )
        for buggy in non_finishers:
            buggy.position = next_finisher_position
            next_finisher_position += 1

    top_dogs = finishers.copy()
    if is_dnf_a_position:
        top_dogs += non_finishers.copy()
    if top_dogs:
        sleep(1) # pause in case you've been bouncing on the ENTER key
        podium_size = 1 if len(top_dogs) ==  1 else input_integer(
            name="podium size",
            default=len(top_dogs),
            minimum=0,
            prompt=f"Want to see the result summary... for how many of the {len(top_dogs)} buggies?"
        )
        if podium_size:
            if podium_size < len(top_dogs):
                msg = f"Results summary: top racers {podium_size} (of {len(top_dogs)}) on the podium:"
            else:
                msg = "Results summary: this is all the racers on the podium:"
            print(f"\n[ ] {msg}")
            print(f"[ ] {'=' * len(msg)}")
            last_pos = None
            for index, b in enumerate(top_dogs):
                dnf = "(DNF)" if b not in finishers else ""
                eq = "=" if b.position == last_pos else ""
                print(f"[★] {eq:1}{b.position:-2} {dnf:5}  {b.username}")
                last_pos = b.position
                if index + 1 == podium_size:
                    break
            print()
    else:
        print("[ ] no buggies got a position on the podium: maybe rerun it?")
        print("[!] you cannot upload a race with no results...")
        print("[!] ...but (up on the server) you can edit the race and declare it abandoned")
    results = {
      "race_file_url": race_data.get("race_file_url") or "",
      "title": race_data.get("title") or "",
      "description": race_data.get("description") or "",
      "cost_limit": cost_limit,
      "max_laps": max_laps,
      "track_image_url": race_data.get("track_image_url") or "",
      "track_svg_url": race_data.get("track_svg_url") or "",
      "svg_path_length": svg_path_length,
      "lap_length": lap_length,
      "league": race_data.get("league"),
      "start_at": race_data.get("start_at") or "",
      "raced_at": race_start_at,
      "is_dnf_position": is_dnf_a_position,
      "buggies_entered": len(buggies_entered),
      "buggies_started": len(buggies),
      "buggies_finished": len(finishers),
      "buggies": RacingBuggy.get_json_list_of_buggies(buggies_entered),
      "events": [RaceEvent.get_list_of_events(events_in_step) for events_in_step in events],
      "version": "1.1"
    }
    jsonfilename = DEFAULT_RESULTS_FILENAME
    print(f"[ ] opening results JSON file \"{jsonfilename}\"... ")
    jsonfile = open(jsonfilename, "w")
    print(json.dumps(results, indent=2), file=jsonfile)
    jsonfile.close()    
    print(f"[ ] wrote to \"{jsonfilename}\", ready to upload")

def main():
    print("[ ] Get ready to race!")
    buggies = None
    race_data = {}
    if opts.no_race_file:
        print("[ ] running without a race-file for input (because -n option)")
    else:
        try:
            race_data = load_race_file()
        except FileNotFoundError as e:
            print(f"\n[!] File not found: {e}")
            exit()
        if not race_data.get("buggies"):
            print(
                "[ ] race file does not contain buggies: will try to read them "
                "from a CSV instead"
            )
    # get race_data values


    if not race_data.get("buggies"):
        if race_data is None:
            print
        try:
            buggies = load_csv()
        except FileNotFoundError as e:
            print(f"\n[!] File not found: {e}")
            quit()
        except ValueError as e:
            print(f"\n[!] Problem in CSV: {e}")
            quit()
        race_data["buggies"] = buggies
    run_race(race_data)
    print(f"[.] bye")

if __name__ == "__main__":
    main()