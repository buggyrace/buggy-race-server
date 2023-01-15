AUTHOR = 'buggyrace'
SITENAME = 'buggyrace'
SITEURL = ''
STATIC_PATHS=("assets/css", "assets/img")
PATH = 'content'
THEME = 'buggy-theme'
RELATIVE_URLS = False
SLUGIFY_SOURCE="basename"
PAGE_PATHS = ['tech-notes']
TAG_SAVE_AS = ''
TIMEZONE = 'Europe/London'
DEFAULT_LANG = 'en'
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
LINKS = ()
SOCIAL = ()
DEFAULT_PAGINATION = False

DIRECT_TEMPLATES = []
#PAGE_URL = '{slug}'
#PAGE_SAVE_AS = '{slug}.html'

JINJA_GLOBALS={
  "BUGGY_RACE_SERVER_URL": "http://localhost:8000",
  "BUGGY_EDITOR_GITHUB_URL": "https://github.com/buggyrace/buggy-race-editor",
  "XXX": "fixme-123"
}
PROJECT_CODE = "CS888"
# BUGGY_RACE_SERVER_URL = "http://localhost:8000"
# BUGGY_EDITOR_GITHUB_URL = "https://github.com/buggyrace/buggy-race-editor"
# PROJECT_REPORT_TYPE = "poster"

CACHE_CONTENT = False