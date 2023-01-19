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

JINJA_GLOBALS={
#  "BUGGY_RACE_SERVER_URL": "http://localhost:8000",
#  "BUGGY_EDITOR_GITHUB_URL": "https://github.com/buggyrace/buggy-race-editor",
  "PROJECT_CODE": "CS888",
  "PROJECT_REPORT_TYPE": "poster"
}

