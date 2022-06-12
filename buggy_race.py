# run buggy race with the flask shell
# You need to have a buggy CSV file, downloaded from the server
# — you'll be asked for the filename (buggies.csv is the default)
# 
# FLASK_ENV=development flask shell
# >>> import buggy_race
# >>> buggy_race.load_csv()
#
# this puts the buggies into the database (required because we're using
# the Flask models, i.e., via the ORM)
#
# then do
#
# >>> buggy_race.run_race()
#
# You'll be asked for a cost (points) threshhold for this race.
# A list of buggies who do not qualify for the race is produced, together
# with the rule or rules they violated.
# This is dumped out into `race.log`
# Then it runs the race using the qualifying buggies.
# It *should* produce a log that, later, a JavaScript/WebASM process in the
# browser could replay as an animation, etc.
#
# Yes it's a manual process for now and this script was never finished!

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
DEFAULT_COST_THRESHHOLD = 1000
DEFAULT_MAX_CLICKS = 2000 # limit this to prevent races going on too long

DEFAULT_PK_OF_PUNCTURE = { # probability of event in 1000
  "knobbly":   3,
  "slick":     6,
  "steelband": 2,
  "reactive":  1,
  "maglev":    0
}

def load_csv(csv_filename=None):
  buggies = Buggy.query.all()
  print("[ ] Read {} buggies from database".format(len(buggies)))
  if csv_filename is None or csv_filename == '':
    csv_filename = str(input("[?] Filename of buggy data in CSV: [{}] ".format(DEFAULT_CSV_FILENAME))).strip()
  if csv_filename == "":
    print("[ ] defaulting to {}".format(DEFAULT_CSV_FILENAME))
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
    print("[+] read data for {} buggies".format(len(buggy_data)))
    for b in buggy_data:
      print("[ ]    {:>3s} {}".format(b["id"], b["username"]))
    if len(buggies):
      y_or_n = str(input("[?] Delete existing {} buggies? [yN] ".format(len(buggies)))).strip()
      if y_or_n.lower() != 'y':
        print("[!] OK: quitting, database unchanged")
        return
      print("[ ] OK deleting old data:")
      Buggy.query.delete();
      buggies = Buggy.query.all()
      print("[ ] done: now {} buggies in database".format(len(buggies)))
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
          active=True,
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
  print("[ ] database now contains {} buggies".format(len(buggies)))


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
    self.nom = "[" + self.initials + "]"

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
        self.power_units -= 1 # FIXME rate of consumption?
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
  print("[ ] Read {} buggies from database".format(len(records)))
  cost_threshhold = 0
  while cost_threshhold < 1:
    cost_threshhold = str(
      input("[?] Maximum buggy cost for this race? [{}] ".format(DEFAULT_COST_THRESHHOLD))).strip()
    if cost_threshhold == '':
      cost_threshhold = DEFAULT_COST_THRESHHOLD
    else:
      try:
        cost_threshhold = int(cost_threshhold)
      except ValueError:
        print("[!] integer greater than 1 needed")
        cost_threshhold = 0
  print("[ ] race threshhold: {}".format(cost_threshhold))
  max_clicks = 0
  while max_clicks < 1:
    max_clicks = str(
      input("[?] Maximum time clicks for this race? (bail out after this) [{}] ".format(DEFAULT_MAX_CLICKS))).strip()
    if max_clicks == '':
      max_clicks = DEFAULT_MAX_CLICKS
    else:
      try:
        max_clicks = int(max_clicks)
      except ValueError:
        print("[!] integer greater than 1 needed")
        max_clicks = 0
  
  logfilename = DEFAULT_RACE_FILENAME
  print("[ ] opening race log file {}... ".format(logfilename))
  logfile = open(logfilename, "w")
  logfile.write("# race cost<={} run at {}\n".format(
    cost_threshhold, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
  print("[ ] Checking race rules...")
  buggies = []
  qty_violators = 0
  for b in records:
    buggy = RacingBuggy(b)
    buggy.set_rule_violations(cost_threshhold)
    if buggy.violations is not None:
      qty_violators += 1
      print("[ ]    {:3d} {:24s} {:6s} {:3d} {:20s}".format(
        buggy.id, buggy.usernick, buggy.initials,
        buggy.qty_wheels, buggy.buggy.flag_color)
      )
      print("[-]    violates: {}".format(", ".join(buggy.violations)))
      logfile.write("VIOLATION: {},{}\n".format(buggy.username, ",".join(buggy.violations)))
    else:
      buggies.append(buggy)
  print("[*] {} buggies are excluded due to race rule violations".format(qty_violators))
  logfile.write("#\n")
  print("[ ] next: {} buggies ready to start the race:".format(len(buggies)))
  for b in buggies:
    logfile.write("ENTRANT: {},{},{},{},{}\n".format(
      b.username, b.initials,
      b.buggy.flag_color, b.buggy.flag_pattern, b.buggy.flag_color_secondary
    ))
  logfile.write("#\n")
  if len(buggies) == 0:
    logfile.write("# race abandoned: no buggies available to run\n")
    print("[!] race abandoned")
    return
  logfile.write("# race starts...\n")
  print(" [ ] GO!")
  clicks = 0
  winners = []
  def racelog(rb, msg):
    print("{:4d} {} {}".format(clicks, rb.nom, msg))

  while clicks < max_clicks:
    clicks += 1
    for b in buggies:
      if b.is_parked:
        continue
      if pk(1) and pk(b.buggy.mass/b.buggy.qty_wheels):
        racelog(b, "catastrophic chassis failure: buggy breaks. End of race.")
        b.is_parked = True
      if pk(DEFAULT_PK_OF_PUNCTURE[b.buggy.tyres] * b.qty_good_wheels):
        b.suffer_puncture()
        punc_str = "use spare: still" if b.qty_good_wheels == b.qty_wheels else "now"
        racelog(b, "puncture! {} running on {} of {} wheels".format(
          punc_str, b.qty_good_wheels, b.qty_wheels))
      
      power = b.power_in_use()
      if power is not None:
        b.consume_power()
        #racelog(b, "power {} consumed (units {})".format(power, b.power_units))
        new_power = b.power_in_use()
        if  new_power != power:
          if new_power is None:
            racelog(b, "ran out of {} power".format(power))
          else:
            racelog(b, "switched to auxiliary power {}".format(new_power))
          
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
  logfile.close()
  print("[:] race ends after {} clicks".format(clicks))
  print("[ ] see race log in {}".format(logfilename))

