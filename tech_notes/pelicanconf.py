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
SOCIAL = ()
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
  "SOCIAL_0_NAME": "",
  "SOCIAL_0_TEXT": "",
  "SOCIAL_0_URL": "",
  "SOCIAL_1_NAME": "",
  "SOCIAL_1_TEXT": "",
  "SOCIAL_1_URL": "",
  "SOCIAL_2_NAME": "",
  "SOCIAL_2_TEXT": "",
  "SOCIAL_2_URL": "",
  "SOCIAL_3_NAME": "",
  "SOCIAL_3_TEXT": "",
  "SOCIAL_3_URL": "",
  "TASK_NAME_FOR_API": "4-API",
  "TASK_NAME_FOR_VALIDATION": "1-VALID",
  "WANT_FAKE_LATEX": 0,
}
