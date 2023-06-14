# run buggy race
#================

# Does not require access to database, etc: just the race_specs.py
# from buggy_race_server.lib (for the shared specifications)

# Doing it this way for now so no load on production server
# and can run as many times here as wanted
#
# Before you start:
#   * Download the a buggy CSV file from the race server
#
# When you've finished:
#
#   * on race server: admin → races → [select race] → upload results
#   * check the warnings (if any) are acceptable
#   * if there were warnings, either:
#      * edit the JSON to fix them
#      * upload again, this time with "ignore warnings"
#
#   * (TODO): (not implemented; and even then maybe optional):
#     publish the race log, buggies.csv and result log and add their
#     URLs by editing the race.
#     These three files are needed to _replay_ the race.
#
import os
import sys
import csv
import json
import re
from datetime import datetime, timezone # will need locale really
from random import randint
from enum import Enum

sys.path.append(os.path.join(os.path.dirname(__file__), '..', ''))
from buggy_race_server.lib.race_specs import BuggySpecs

DEFAULT_RACE_FILENAME_JSON = 'race.json'

DEFAULT_CSV_FILENAME = 'cs1999-buggies-2023-06-07-FOURTH-RACE-STUDENTS.csv' # 'buggies.csv'
DEFAULT_RACE_FILENAME = 'race.log'
DEFAULT_RESULTS_FILENAME = 'race-results.json'
DEFAULT_EVENT_LOG_FILENAME = "race-events.json"
DEFAULT_COST_LIMIT = 100 # 200
DEFAULT_INITIAL_STEPS = 100
DEFAULT_MORE_STEPS =  10
DEFAULT_MAX_LAPS = 1
DEFAULT_LAP_LENGTH = 355

DEFAULT_PK_OF_PUNCTURE = {
    "knobbly":   3,
    "slick":     6,
    "steelband": 2,
    "reactive":  1,
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
    PUNCTURE = "p"
    CHASSIS_FAIL = "xc"

def pk(prob): # probability in 1000
    return randint(0, 1000) < prob

def distance_by_power(power_type):
    return 3 + randint(1 ,6) +  randint(1, 6)

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

    def __str__(self):
        return f"<{self.username}>"

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
        self.d += delta

    def consume_power(self):
        pwr = self.power_in_use()
        msg = None
        if pwr is not None:
            if BuggySpecs.POWER_TYPES[pwr]['consum']:
                if self.power_units > 0:
                    # have not run out of power
                    self.power_units -= POWER_DATA[pwr]['rate'] * (randint(0, 10)/50)
                    self.advance(pwr)
                    if pwr == "hamster" and self.hamster_booster > 0 and pk(10):
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
        raise FileNotFoundError(f"can't find JSON file containing race data ({json_filename}) ")
    try:
        with open(json_filename, "r") as read_file:
            race_data = json.load(read_file)
    except UnicodeDecodeError as e:
        print("[!] Encoding error (maybe that wasn't a good JSON file?)")
        quit()
    except json.decoder.JSONDecodeError as e:
        print("[!] Failed to parse JSON data:\n    {e}")
        quit()
    buggy_data = race_data["buggies"]
    race_data["buggies"] = []
    print("[ ] Processing: ", end="")
    for i, buggy_data in enumerate(buggy_data):
        for k in BuggySpecs.DEFAULTS:
            if k not in buggy_data:
               raise ValueError(f"column/key \"{k}\" is missing from CSV (buggy {i})")
            if buggy_data[k] == '': # anomaly of CSV dumping: tidy nones
                buggy_data[k] = None
            if type(BuggySpecs.DEFAULTS[k]) == bool:
                print(f"{k} is boolean! ({buggy_data[k]})")
                if type(buggy_data[k]) != bool:
                    buggy_data[k] = buggy_data[k].lower() == "true"
        race_data["buggies"].append(RacingBuggy(buggy_data))
        print(".", end="", flush=True)
    return race_data

def load_csv(csv_filename=None):
    if csv_filename is None or csv_filename == '':
        csv_filename = str(input(f"[?] Filename of buggy data in CSV: [{DEFAULT_CSV_FILENAME}] ")).strip()
    if csv_filename == "":
        print(f"[ ] defaulting to {DEFAULT_CSV_FILENAME}")
        csv_filename = DEFAULT_CSV_FILENAME
    if not os.path.isfile(csv_filename):
        raise FileNotFoundError(f"can't find CSV file containing buggy data (csv_filename) ")
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

    print(f"[ ] buggies entered for this race (i.e., from CSV): {len(buggies_entered)}")
    cost_limit = 0
    while cost_limit < 1:
        cost_limit = str(
            input(f"[?] Maximum buggy cost for this race? [{DEFAULT_COST_LIMIT}] ")).strip()
        if cost_limit == '':
            cost_limit = DEFAULT_COST_LIMIT
        else:
            try:
                cost_limit = int(cost_limit)
            except ValueError:
                print("[!] integer greater than 1 needed")
                cost_limit = 0
    print(f"[ ] race cost limit: {cost_limit}")

    max_laps = 0
    while max_laps < 1:
        max_laps = str(
            input(f"[?] Number of laps for this race? [{DEFAULT_MAX_LAPS}] ")).strip()
        if max_laps == '':
            max_laps = DEFAULT_MAX_LAPS
        else:
            try:
                max_laps = int(max_laps)
            except ValueError:
                print("[!] integer greater than 1 needed")
                max_laps = 0
    print(f"[ ] race laps: {max_laps}")

    lap_length = 0
    while lap_length < 1:
        lap_length = str(
            input(f"[?] Lap length? [{DEFAULT_LAP_LENGTH}] ")).strip()
        if lap_length == '':
            lap_length = DEFAULT_LAP_LENGTH
        else:
            try:
                lap_length = int(lap_length)
            except ValueError:
                print("[!] integer greater than 1 needed")
                lap_length = 0
    print(f"[ ] lap length: {lap_length}")

    pretty_race_length = f"{max_laps} lap race"

    logfilename = DEFAULT_RACE_FILENAME
    print(f"[ ] opening race log file {logfilename}... ")
    logfile = open(logfilename, "w")
    race_start_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    logfile.write(f"# race cost<={cost_limit} run at {race_start_at}\n")
    print("[ ] Checking race rules...")
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
            print(f"[ ]    {buggy.nom} {buggy.qty_wheels}×o ({buggy.qty_tyres}) {buggy.flag_color} £{buggy.total_cost}")
            print(f"[-]    violates: {'+'.join(buggy.violations)}")
            logfile.write(f"VIOLATION: {buggy.username},{'+'.join(buggy.violations)}\n")
        else:
            buggy.position = 0
            buggies.append(buggy)
    print(f"[*] {qty_violators} buggies are excluded due to race rule violations")
    logfile.write("#\n")
    print(f"[ ] next: {len(buggies)} buggies ready to start the race:")
    print("[ ]       " + ", ".join([b.username for b in buggies]))
    for b in buggies:
        logfile.write(f"ENTRANT: {b.username},{b.flag_color},{b.flag_pattern},{b.flag_color_secondary}\n")
    logfile.write("#\n")
    finishers = []
    if len(buggies) == 0:
        logfile.write("# race abandoned: no buggies available to run\n")
        print("[!] race abandoned because nobody entered it")
    else:
        logfile.write("# race starts...\n")
        print("[ ] GO!")
        steps = 0
        max_steps = DEFAULT_INITIAL_STEPS 

        while steps < max_steps:
            events_this_step = []
            next_finisher_position += finishers_this_step # 2 buggies tie, next one is 3rd
            finishers_this_step = 0
            steps += 1
            print(f"------------------------ step {steps} ------------------------")
            qty_active = 0
            for buggy in buggies:
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
                        if buggy.qty_good_wheels == 0:
                            punc_str = "no tyres left: parked"
                        else:
                            punc_str = "use spare: still" if buggy.qty_good_wheels == buggy.qty_wheels else "now"
                            punc_str += f" running on {buggy.qty_good_wheels} of {buggy.qty_wheels} wheels"
                        racelog(
                            buggy=buggy,
                            event_type=EventType.PUNCTURE,
                            msg="puncture! " + punc_str
                        )
                        #   ? risk of primary power fail?
                        #   data[id]["attacks"] > 0?
                        #     anyone near? chance of attack?
                        #     target defensive? steady?
                        #        ? chance of attack backfire
                        #          calculate damage of attack
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
                            msg=f"crosses the finish line in {position_str} ({pretty_race_length})"
                        )
                        buggy.d += score_from_dice("3d4") # nudge over line
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

        logfile.close()
        print(f"[:] race ends after {steps} steps")
        non_finishers = sorted(
            [buggy for buggy in buggies if buggy.position == 0 ],
            key=lambda buggy: buggy.d,
            reverse=True
        )
        for buggy in non_finishers:
            buggy.position = next_finisher_position
            next_finisher_position += 1

    print(f"[ ] see race log in {logfilename}")

    # for events_in_step in events:
    #     json_events.append(
    #         "    [\n"
    #         + ",\n".join([ev.to_json() for ev in events_in_step])
    #         + "\n    ]"
    #     )

    results = {
 
      "result_log_url": race_data["result_log_url"],
      "title": race_data["title"],
      "description": race_data["description"],
      "cost_limit": cost_limit,
      "max_laps": max_laps,
      "track_image_url": race_data["track_image_url"],
      "track_svg_url": race_data["track_svg_url"],
      "race_log_url": race_data["race_log_url"],
      "league": race_data["league"],
      "start_at": race_data["start_at"],
      "raced_at": race_start_at,
      "buggies_entered": len(buggies_entered),
      "buggies_started": len(buggies),
      "buggies_finished": len(finishers),
      "buggies": RacingBuggy.get_json_list_of_buggies(buggies_entered),
      "events": [RaceEvent.get_list_of_events(events_in_step) for events_in_step in events],
      "version": "1.0"
    }
    jsonfilename = DEFAULT_RESULTS_FILENAME
    print(f"[ ] opening results JSON file {jsonfilename}... ")
    jsonfile = open(jsonfilename, "w")
    print(json.dumps(results, indent=2), file=jsonfile)
    jsonfile.close()
    print(f"[ ] wrote to {jsonfilename}, ready to upload")
    print(f"[.] bye")

    # jsonfilename = DEFAULT_EVENT_LOG_FILENAME
    # print(f"[ ] opening events JSON file {jsonfilename}... ")
    # jsonfile = open(jsonfilename, "w")
    # print('{\n "events": [', file=jsonfile)
    # print(",\n".join(json_strings), file=jsonfile)
    # print('  ]\n}', file=jsonfile)
    # jsonfile.close()
    # print(f"[ ] wrote to {jsonfilename}, ready to upload")

    print(f"[.] bye")

def main():
    print("[ ] Ready to race!")
    buggies = None
    try:
        race_data = load_race_file()
    except FileNotFoundError as e:
        print(f"\n[!] File not found: {e}")
    if not race_data.get("buggies"):
        print("[ ] Race file does not contain buggies: will try to read them from a CSV instead")
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

if __name__ == "__main__":
    main()