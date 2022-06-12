# For notifying students of their login credentials using Moodle's
# feedback mechanism: it's a way to "easily" send the personalised
# login credentials to each enrolled student.
# Advantage: it's on the Moodle so all staff can access it
# Disadvantage: it's on the Moodle :-(
#
# You need:
#
# * set up an assignment on the Moodle with these settings:
#   - Title: Race server logins
#   - Desc: This "assignment" does not require any input from you
#           the student — it's where you'll find your personal login
#           and password on the race server.
#   - Disable all dates on Availability (you don't care, I think)
#   - Submission types: disable _all_ (there's no submission)
#   - Feeback types: (this is the crucial bit)
#       + Feedback comments
#       + Offline grading worksheet
#   - Notifications: disable all (maybe announce in the forum instead)
#   - Grade: None (if you don't specify "no grade" like this, Moodle
#            might decide not to let the student seen the feedback until
#            you've also given them a grade, sigh)
#   
# Then you can go to the assignment, view all submissions (there won't
# be any, of course)... but that give you access to "Grade actions:"
# and you can "Download grading worksheet"
# (if you don't see this option, you missed "offline grading worksheet"
# as a feedback type option in the settings).
# Download that CSV: that's what you're going to populate with the 
# username/password message, and then upload.
#
# You also need a CSV file of: email, username, password
#    (this should really be the same file as the one you used for bulk
#    registration, sorry TODO)
#
# This python script reads the two spreadies and produces a new one
# with the username/passwords added as feedback to the grading sheet
# that you can then upload to the Moodle.
#
# Faking by hand
# --------------
# If you need to add a single user (this happened in 2021 resits)
# you can manually make the upload file by downloading the grading
# worksheet and deleting all students except the one you want to
# notify/update. Check the format matches, but in general you're
# aiming to have a file that looks something like this:
#
# Identifier,Full name,Email address,Status,Grade,Grade can be changed,Last modified (grade),Feedback comments
# Participant 123456,Jane Holloway,Jane.Holloway.2020@live.rhul.ac.uk,,,Yes,-,"
# Your <a href=""https://rhul.buggyrace.net"">Buggy Race Server</a> login:
# <ul>
# <li>username: jane</li>
# <li>password: purplehorse82 </li>
# </ul>
# Change your password after you've logged in."
#

import csv
from environs import Env

env = Env()
env.read_env()
server_url = env.str("BUGGY_RACE_SERVER_URL")

MOODLE_GRADING_CSV = 'Grades-CS1999-202122-Race server logins-650926.csv'
EMAIL_UN_PW_CSV = 'email-un-pw.csv'

OUTPUT_CSV = 'for-moodle-upload.csv'

NUMBER_OF_COLUMNS = 3 # email, username, password

MOODLE_EMAIL_INDEX = 2 # 3rd column of download spreadie is email
MOODLE_NUMBER_OF_COLUMNS = 8 # expected structure of download spreadie


# read the email/username/pw one

usernames_by_email = {}
passwords_by_email = {}

def make_message(email):
    return f"""
Your <a href="{server_url}">Buggy Race Server</a> login:
<ul>
<li>username: {usernames_by_email[email]} </li>
<li>password: {passwords_by_email[email]} </li>
</ul>
Change your password after you've logged in.
"""


line_no = 0
print(f"[ ] racing server URL is: {server_url}")
print(f"[ ] reading EMAIL_UN_PW_CSV...")
with open(EMAIL_UN_PW_CSV, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',')
    for row in csv_reader:
        line_no += 1
        if len(row) != NUMBER_OF_COLUMNS:
            print(f"[!] line {line_no}: has rows: {len(row)} ≠ {NUMBER_OF_COLUMNS}")
        else:
          email = row[0].lower()
          if '@' in email:
              usernames_by_email[email] = row[1]
              passwords_by_email[email] = row[2]
          else:
            print(f"[!] line {line_no}: no @-sign in email")
print(f"[ ] done ({line_no} lines)")

new_csv = open(OUTPUT_CSV, mode='w')
csv_writer = csv.writer(new_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

line_no = 0
print(f"[ ] reading {MOODLE_GRADING_CSV}...")
with open(MOODLE_GRADING_CSV, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',')
    line_no = 0
    for row in csv_reader:
        line_no += 1
        if len(row) != MOODLE_NUMBER_OF_COLUMNS:
            print(f"[!] line {line_no}: no @-sign in email")
        else:
          email = row[MOODLE_EMAIL_INDEX].lower()
          if '@' in email:
              if email in usernames_by_email:
                  row[-1] = make_message(email)
              else:
                  print(f"[!] no entry for {email}")
          csv_writer.writerow(row)
print(f"[ ] done ({line_no} lines)")
print(f"[ ] OK: \"{OUTPUT_CSV}\" is ready for upload to moodle")

