# run buggy race with the flask shell
#
# Doing it this way for now so no load on production server
# and can run as many times here as wanted
# Manual process for now
#
# If you're running this locally, before you run the first time:
#
#  * set up environment stuff: cp env.example to .env and edit it
#  * (it should run fine with sqlite, i.e., no complex database config needed)
#  * create the database with:
#       flask db init
#       flask db migrate
#       flask db upgrade
#  * make sure you have a buggies.csv to hand (download one from the race
#    server if necessary)
#  * now you can run this script:
#
#       FLASK_ENV=development flask shell
#       >>> from utils import run_buggy_race
#       >>> run_buggy_race.load_csv()
#       >>> run_buggy_race.run_race()

#       synonyms:
#
#       FLASK_ENV=development flask shell
#       >>> from utils import run_buggy_race as r
#       >>> r.l()
#       >>> r.r()
#
#
import json
import os.path
import sys
import csv
from datetime import datetime
from random import randint
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.user.models import User

DEFAULT_RACE_FILENAME = 'race.log'
DEFAULT_CSV_FILENAME = 'buggies.csv'
DEFAULT_COST_THRESHHOLD = 200
DEFAULT_INITIAL_CLICKS = 1000
DEFAULT_MORE_CLICKS =  300

DEFAULT_PK_OF_PUNCTURE = {
  "knobbly":   3,
  "slick":     6,
  "steelband": 2,
  "reactive":  1,
  "maglev":    0
}

def load_csv(csv_filename=None):
  buggies = Buggy.query.all()
  print(f"[ ] Read {len(buggies)} buggies from database")
  if csv_filename is None or csv_filename == '':
    csv_filename = str(input(f"[?] Filename of buggy data in CSV: [{DEFAULT_CSV_FILENAME}] ")).strip()
  if csv_filename == "":
    print(f"[ ] defaulting to {DEFAULT_CSV_FILENAME}")
    csv_filename = DEFAULT_CSV_FILENAME
  if not os.path.isfile(csv_filename):
    print("[!] no such file, quitting")
    return
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
    for b in buggy_data:
      print(f"[ ]    {b['username']}")
    if len(buggies):
      y_or_n = str(input("f[?] Delete existing {len(buggies)} buggies? [Yn] ")).strip()
      if y_or_n.lower() == 'n':
        print("[!] OK: quitting, database unchanged")
        return
      print("[ ] OK deleting old data:")
      Buggy.query.delete();
      buggies = Buggy.query.all()
      print("[ ] done: now {len(buggies)} buggies in database")
    print("[ ] inserting buggies:", end="", flush=True)
    for b in buggy_data:
      username = b.pop("username")
      user = User.query.filter_by(username=username).first()
      b.pop("id")
      b.pop("created_at")
      if user is None:
        email = username if '@' in username else str(randint(1000, 9999))+"@example.com"
        user = User.create(
          username=username,
          email=email,
          password='password',
          is_active=True,
        )
        #print("[:] read user: {} id={}".format(newbie.username, newbie.id ))
      b["user_id"]=user.id
      for k in Buggy.DEFAULTS:
        if b[k] == 'none' or b[k] == '': # anomaly of CSV dumping: tidy nones
          b[k] = None
        if type(Buggy.DEFAULTS[k]) == bool:
          # print("{} is boolean! ({})".format(k, b[k]))
          b[k] = b[k].lower() == "true"
      new_buggy = Buggy.create(**b)
      print(".", end="", flush=True)
    print(" OK")
  buggies = Buggy.query.all()
  print(f"[ ] database now contains {len(buggies)} buggies")


def pk(prob): # prob in 1000
  return randint(0, 1000) < prob

class RacingBuggy():
  def __init__(self, source_buggy):
    self.buggy = source_buggy
    self.buggy.calculate_total_cost()
    self.id = source_buggy.id
    self.qty_wheels = source_buggy.qty_wheels
    self.qty_good_wheels = self.qty_wheels
    self.user = User.query.filter_by(id=source_buggy.user_id).first()
    self.username = self.user.username
    self.usernick = self.username.partition("@")[0]
    self.initials = ".".join([s[0].upper() for s in list(
      filter(lambda x: (x[0].isalpha()), self.usernick.split(".")))])+"."
    self.d = 0   # distance from start
    self.a = 0   # acceleration
    self.s = 0   # speed
    self.power_units = source_buggy.power_units
    self.qty_attacks = source_buggy.qty_attacks
    self.qty_tyres = source_buggy.qty_tyres
    self.mass = source_buggy.mass
    self.is_on_aux = False
    self.is_parked = False
    self.violations = None
    self.nom = "[" + self.username + "]"

  def power_in_use(self):
    if self.is_parked:
      return None
    elif self.is_on_aux:
      return self.buggy.aux_power_type
    else:
      return self.buggy.power_type

  def consume_power(self):
    pwr = self.power_in_use()
    if pwr is not None and Buggy.POWER_TYPES[pwr]['consum']:
      if self.power_units > 0:
        self.power_units -= 0.2 # FIXME rate of consumption?
        # FIXME reduced mass
      else:
        if self.is_on_aux or self.buggy.aux_power_type is None:
          self.is_parked = True
        else:
          self.power_units = self.buggy.aux_power_units
          self.is_on_aux = True

  def suffer_puncture(self):
    self.qty_tyres -= 1
    if self.qty_tyres < self.qty_good_wheels:
      self.qty_good_wheels = self.qty_tyres
    if self.qty_tyres == 0:
      self.is_parked = True
    
  def set_rule_violations(self, cost_threshhold):
    self.violations = self.buggy.get_rule_violations(cost_threshhold)

def run_race():
  records = Buggy.query.all()
  print(f"[ ] Read {len(records)} buggies from database")
  cost_threshhold = 0
  while cost_threshhold < 1:
    cost_threshhold = str(
      input(f"[?] Maximum buggy cost for this race? [{DEFAULT_COST_THRESHHOLD}] ")).strip()
    if cost_threshhold == '':
      cost_threshhold = DEFAULT_COST_THRESHHOLD
    else:
      try:
        cost_threshhold = int(cost_threshhold)
      except ValueError:
        print("[!] integer greater than 1 needed")
        cost_threshhold = 0
  print(f"[ ] race threshhold: {cost_threshhold}")
  logfilename = DEFAULT_RACE_FILENAME
  print(f"[ ] opening race log file {logfilename}... ")
  logfile = open(logfilename, "w")
  logfile.write(f"# race cost<={cost_threshhold} run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
  print("[ ] Checking race rules...")
  buggies = []
  qty_violators = 0
  for b in records:
    buggy = RacingBuggy(b)
    buggy.set_rule_violations(cost_threshhold)
    if buggy.violations is not None:
      qty_violators += 1
      print(f"[ ]    {buggy.nom} {buggy.qty_wheels}×o {buggy.buggy.flag_color}")
      print(f"[-]    violates: {'+'.join(buggy.violations)}")
      logfile.write(f"VIOLATION: {buggy.username},{'+'.join(buggy.violations)}\n")
    else:
      buggies.append(buggy)
  print(f"[*] {qty_violators} buggies are excluded due to race rule violations")
  logfile.write("#\n")
  print(f"[ ] next: {len(buggies)} buggies ready to start the race:")
  for b in buggies:
    logfile.write(f"ENTRANT: {b.username},{b.buggy.flag_color},{b.buggy.flag_pattern},{b.buggy.flag_color_secondary}\n")
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

  def racelog(rb, msg):
    text = f"{clicks:=5} {rb.nom:12s} {msg}"
    print(text)
    print(text, file=logfile)

  while clicks < max_clicks:
    clicks += 1
    qty_active = 0
    for b in buggies:
      if b.is_parked:
        continue
      qty_active += 1
      if pk(1) and pk(b.buggy.mass/b.buggy.qty_wheels):
        racelog(b, "catastrophic chassis failure: buggy breaks.")
        b.is_parked = True
      if pk(DEFAULT_PK_OF_PUNCTURE[b.buggy.tyres] * b.qty_good_wheels):
        b.suffer_puncture()
        if b.qty_good_wheels == 0:
          punc_str = "no tyres left: parked"
        else:
          punc_str = "use spare: still" if b.qty_good_wheels == b.qty_wheels else "now"
          punc_str += f" running on {b.qty_good_wheels} of {b.qty_wheels} wheels"
        racelog(b, f"puncture! {punc_str}")
      
      power = b.power_in_use()
      if power is not None:
        b.consume_power()
        #racelog(b, "power {} consumed (units {})".format(power, b.power_units))
        new_power = b.power_in_use()
        if  new_power != power:
          if new_power is None:
            racelog(b, f"ran out of {power} power")
          else:
            racelog(b, f"ran out of {power}, switched to auxiliary power {new_power}")
          
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

def l():
  load_csv()
def r():
  run_race()

