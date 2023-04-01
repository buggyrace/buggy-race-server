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
from datetime import datetime
from random import randint

sys.path.append(os.path.join(os.path.dirname(__file__), '..', ''))
from buggy_race_server.lib.race_specs import BuggySpecs

DEFAULT_CSV_FILENAME = 'buggies.csv'
DEFAULT_RACE_FILENAME = 'race.log'
DEFAULT_RESULTS_FILENAME = 'buggies.json'
DEFAULT_COST_LIMIT = 200
DEFAULT_INITIAL_CLICKS = 1000
DEFAULT_MORE_CLICKS =  300

DEFAULT_PK_OF_PUNCTURE = {
    "knobbly":   3,
    "slick":     6,
    "steelband": 2,
    "reactive":  1,
    "maglev":    0
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
                creator = RacingBuggy.ATTRIB_TYPES[k] # e.g., str, int, bool
                if creator == str: # check value is a member
                    kk = "power_type" if k == "aux_power_type" else k
                    if kk in RacingBuggy.GAME_DATA: # do we have members?
                        if buggy_data[k] not in RacingBuggy.GAME_DATA[kk]:
                            buggy_data[k] = RacingBuggy.DEFAULTS[k]
                try: # to cast the value to the expected type...
                    self.__setattr__(k, creator(buggy_data[k])) 
                except ValueError: # missing value (or wrong format?)
                    default = RacingBuggy.DEFAULTS.get(k)
                    if default is None:
                        self.__setattr__(k, creator()) # empty default
                    else:
                      self.__setattr__(k, creator(default))
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

    def result_data(self):
        """Data for each buggy that is presented in the `results` section of
        the JSON that is uploaded to the server."""

        return {
            "username": "dave", #self.username,
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
            return self.aux_power_type
        else:
            return self.power_type

    def consume_power(self):
        pwr = self.power_in_use()
        if pwr is not None and BuggySpecs.POWER_TYPES[pwr]['consum']:
            if self.power_units > 0:
                self.power_units -= 0.2 # FIXME rate of consumption?
                # FIXME reduced mass
            else:
                if self.is_on_aux or self.aux_power_type is None:
                  self.is_parked = True
                else:
                  self.power_units = self.aux_power_units
                  self.is_on_aux = True

    def suffer_puncture(self):
        self.qty_tyres -= 1
        if self.qty_tyres < self.qty_good_wheels:
            self.qty_good_wheels = self.qty_tyres
        if self.qty_tyres == 0:
            self.is_parked = True

    def set_rule_violations(self, cost_limit):
        self.violations = self.get_rule_violations(cost_limit)




# ---------------------------------------------------------------------

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
            if len(headers):
                buggy_data.append(row)
            else:
                headers = row.keys()
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

def run_race(buggies_entered):

    def racelog(rb, msg):
        text = f"{clicks:=5} {rb.nom:12s} {msg}"
        print(text)
        print(text, file=logfile)

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
    logfilename = DEFAULT_RACE_FILENAME
    print(f"[ ] opening race log file {logfilename}... ")
    logfile = open(logfilename, "w")
    race_start_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logfile.write(f"# race cost<={cost_limit} run at {race_start_at}\n")
    print("[ ] Checking race rules...")
    qty_violators = 0
    buggies = []
    fake_position = 1
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
            buggy.position = fake_position
            buggies.append(buggy)
            fake_position += 1
    print(f"[*] {qty_violators} buggies are excluded due to race rule violations")
    logfile.write("#\n")
    print(f"[ ] next: {len(buggies)} buggies ready to start the race:")
    for b in buggies:
        logfile.write(f"ENTRANT: {b.username},{b.flag_color},{b.flag_pattern},{b.flag_color_secondary}\n")
    logfile.write("#\n")
    if len(buggies) == 0:
      logfile.write("# race abandoned: no buggies available to run\n")
      print("[!] race abandoned")
      return
    logfile.write("# race starts...\n")
    print("[ ] GO!")
    clicks = 0
    max_clicks = DEFAULT_INITIAL_CLICKS 
    winners = []

    while clicks < max_clicks:
        clicks += 1
        qty_active = 0
        for buggy in buggies:
            if buggy.is_parked:
                continue
            qty_active += 1
            if pk(1) and pk(buggy.mass/buggy.qty_wheels):
                racelog(b, "catastrophic chassis failure: buggy breaks.")
                buggy.is_parked = True
            if pk(DEFAULT_PK_OF_PUNCTURE[buggy.tyres] * buggy.qty_good_wheels):
                buggy.suffer_puncture()
                if buggy.qty_good_wheels == 0:
                    punc_str = "no tyres left: parked"
                else:
                    punc_str = "use spare: still" if buggy.qty_good_wheels == buggy.qty_wheels else "now"
                    punc_str += f" running on {buggy.qty_good_wheels} of {buggy.qty_wheels} wheels"
                racelog(buggy, f"puncture! {punc_str}")
            
            power = buggy.power_in_use()
            if power is not None:
                b.consume_power()
                #racelog(buggy, "power {} consumed (units {})".format(power, buggy.power_units))
                new_power = buggy.power_in_use()
                if new_power != power:
                    if new_power is None:
                        racelog(buggy, f"ran out of {power} power")
                    else:
                        racelog(buggy, f"ran out of {power}, switched to auxiliary power {new_power}")
            
                #   ? risk of primary power fail?

                #   distance travelled x % of tires
                #   data[id][x]+=speed
                #   if data[id][x] > race_distance
                #     winners.append(b)
                #   if len(winnners): bail out
                #   data[id]["attacks"] > 0?
                #     anyone near? chance of attack?
                #     target defensive? steady?
                #        ? chance of attack backfire
                #          calculate damage of attack
            if qty_active == 0:
                print("[ ] no buggies moving...")
                break
            else:
                if clicks == max_clicks:
                    more_clicks = str(
                      input(f"[?] {clicks} clicks so far: add more? [+{DEFAULT_MORE_CLICKS}] ")).strip()
                    if more_clicks == '':
                        more_clicks = DEFAULT_MORE_CLICKS
                    else:
                        try:
                            more_clicks = int(more_clicks)
                        except ValueError:
                            print("[!] integer greater than 1 needed")
                        more_clicks = 0
                    if more_clicks > 0:
                        print(f"[+] running race for another +{more_clicks} clicks")
                    else:
                        print("[-] no more clicks, time is up")
                    max_clicks += more_clicks
    logfile.close()
    print(f"[:] race ends after {clicks} clicks")
    print(f"[ ] see race log in {logfilename}")
    results = {
      # "race_title": "",
      # "cost_limit": 200,
      # "start_at": "2023-03-22 23:58",
      "raced_at": race_start_at,
      "league": "",
      "buggies_entered": len(buggies_entered),
      "buggies_started": len(buggies),
      "buggies_finished": len(buggies),
      # "buggies_csv_url": "https://example.com/buggies223.csv",
      # "race_log_url":  "https://example.com/race-log223.log",
      # "result_log_url" :  "https://example.com/result223.log",
      "results": [buggy.result_data() for buggy in
                    sorted(
                        buggies_entered,
                        key=lambda buggy: (buggy.position, buggy.total_cost, buggy.username)
                    )
                 ],
      "version": "1.0"
    }
    jsonfilename = DEFAULT_RESULTS_FILENAME
    print(f"[ ] opening results JSON file {jsonfilename}... ")
    jsonfile = open(jsonfilename, "w")
    print(json.dumps(results, indent=2), file=jsonfile)
    jsonfile.close()
    print(f"[ ] wrote to {jsonfilename}, ready to upload")
    print(f"[.] bye")

def l():
    load_csv()
def r():
    run_race()


def main():
    print("[ ] Ready to race!")
    buggies = None
    try:
        buggies = load_csv()
    except FileNotFoundError as e:
        print(f"\n[!] File not found: {e}")
    except ValueError as e:
        print(f"\n[!] Problem in CSV: {e}")

    if buggies:
        run_race(buggies)


if __name__ == "__main__":
    main()