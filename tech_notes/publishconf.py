# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
try:
    from pelicanconflive import *
except Exception as e:
    print(f"* failed to read from pelicanconflive.py (maybe not published yet?)")
    print(f"* Problem: {e}")
    print("   - Note: pelicanconflive.py is a copy of pelicanconf.py rewritten immediately")
    print("   - before publication with current config settings in the JINJA_GLOBALS array.")
    # explicitly exit with an error code (as this is called from the main
    # race server as a subprocess)
    sys.exit(1)
    # from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://

RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
