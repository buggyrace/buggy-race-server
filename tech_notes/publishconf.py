# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
try:
  from pelicanconflive import *
except:
  print("* failed to read from pelicanconflive.py (maybe not published yet?) ")
  from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://

RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
