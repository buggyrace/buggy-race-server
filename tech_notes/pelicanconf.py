AUTHOR = 'buggyrace'
SITENAME = 'buggyrace'
SITEURL = ''
STATIC_PATHS=("assets/js", "assets/img")
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
SITES = ()
DEFAULT_PAGINATION = False

# toc ("Table of Contents") extension makes headings linkable
# but... at the expense of the jinja2content — so this isn't
# used and instead we hand-rolled a solution into the
# jinja2content plugin
#
# MARKDOWN = {
#     'extension_configs': {
#         'markdown.extensions.toc': {'anchorlink': True},
#     },
# }

# jinja2content plugin applies jinja substitutions to page (.md) bodies
# as well as the (.html) templates, like Jekyll does: this is necessary
# primarily to get the the gloabl substitutions to apply
PLUGIN_PATHS = ['plugins']
PLUGINS = ['buggyjinja2content']

DIRECT_TEMPLATES = []
CACHE_CONTENT = False

# utils.publish_tech_notes examines this JINJA_GLOBALS and substitutes the
# values with the live (i.e., current config) values: so leave these here
# as a template (even though they mostly contain defaults/empty strings).
JINJA_GLOBALS={
  "BUGGY_RACE_SERVER_URL": "http://localhost:8000",
  "BUGGY_EDITOR_REPO_URL": "https://github.com/buggyrace/buggy-race-editor",
  "BUGGY_EDITOR_REPO_NAME": "buggy-race-editor",
  "BUGGY_EDITOR_REPO_OWNER": "buggyrace",
  "PROJECT_CODE": "",
  "PROJECT_REPORT_TYPE": "report",
  "SITE_1_NAME": "",
  "SITE_1_TEXT": "",
  "SITE_1_URL": "",
  "SITE_2_NAME": "",
  "SITE_2_TEXT": "",
  "SITE_2_URL": "",
  "SITE_3_NAME": "",
  "SITE_3_TEXT": "",
  "SITE_3_URL": "",
  "SITE_4_NAME": "",
  "SITE_4_TEXT": "",
  "SITE_4_URL": "",
  "TASK_NAME_FOR_API": "4-API",
  "TASK_NAME_FOR_VALIDATION": "1-VALID",
  "WANT_FAKE_LATEX": 0,
}
