Tech notes were originally prepared for Jekyll and served via GitHub pages.
They're now hosted by (this) race server by default, using Pelican to generate
the pages (because it's a Python static site generator, avoiding the dependency
on Ruby).

However, if you set the config variable TECH_NOTES_EXTERNAL_URL you can host
your customised tech notes there — in which case, using Jekyll on GitHub
pages is a good solution. If you need it, below is an example of the original
(for Jekyll) _config.yml file that the previous version of the pages used:


theme: jekyll-theme-hacker
title: Buggy Racing tech notes
description: "Tech notes for the Buggy Race Editor"
show_downloads: false

#---------------------------------------------------------------------
# custom URLs:
# these are used within the pages: check they are right!
#---------------------------------------------------------------------
editor_url: https://github.com/buggyrace/buggy-race-editor
race_server_url: https://www.example.com

plugins:
  - jekyll-redirect-from
  - jekyll-optional-front-matter

optional_front_matter:
  remove_originals: true
