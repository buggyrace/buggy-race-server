"""
jinja2content.py
----------------

Pelican plugin that processes Markdown files as jinja templates.

Customised from: https://github.com/pelican-plugins/jinja2content

"""

import os
import re
from tempfile import NamedTemporaryFile

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from pelican import signals
from pelican.readers import HTMLReader, MarkdownReader, RstReader
from pelican.utils import pelican_open


class JinjaContentMixin:

    # Buggy Racing Server custom hack:
    #
    # Linkify headings on the way through
    #
    # note: non-greedy headings here (.*?) are risky if the
    # heading isn't closed properly, *but* we're assuming they
    # will be well-formed because this is coming from markdown
    # ...but to prevent runaways, capping this at 80 chars
    #
    # This adds the class "toclink" as it's mimicking the beahviour
    # of the "toc" markdown extension.
    
    HEADING_LINK_RE = re.compile(
        r"<h(\d)>(.{1,80}?)</h\1>",
        flags=re.IGNORECASE
    )
    HTML_TAGS = re.compile(r"<[^>]+>|&\w+;")
    SLUG_BADCHARS = re.compile(r"[^a-z0-9-]+")
    SLUG_COLLAPSE_HYPHENS = re.compile(r"--+")
    SLUG_TOP_TAIL = re.compile(r"^-|-$")

    def _enhance_heading(matched):
        h_level = matched.group(1)
        text = matched.group(2).strip()
        slug = re.sub(JinjaContentMixin.HTML_TAGS, "-", text.lower())
        slug = re.sub(JinjaContentMixin.SLUG_BADCHARS, '-', slug)
        slug = re.sub(JinjaContentMixin.SLUG_COLLAPSE_HYPHENS, '-', slug)
        slug = re.sub(JinjaContentMixin.SLUG_TOP_TAIL, "", slug)
        return (
            f"<h{h_level} id=\"{slug}\">"
              f"<a href=\"#{slug}\" class=\"toclink\">"
                f"{text}"
              f"</a>"
            f"</h{h_level}>"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # will look first in 'JINJA2CONTENT_TEMPLATES', by default the
        # content root path, then in the theme's templates
        local_dirs = self.settings.get("JINJA2CONTENT_TEMPLATES", ["."])
        local_dirs = [
            os.path.join(self.settings["PATH"], folder) for folder in local_dirs
        ]
        theme_dir = os.path.join(self.settings["THEME"], "templates")

        loaders = [FileSystemLoader(_dir) for _dir in local_dirs + [theme_dir]]
        if "JINJA_ENVIRONMENT" in self.settings:  # pelican 3.7
            jinja_environment = self.settings["JINJA_ENVIRONMENT"]
        else:
            jinja_environment = {
                "trim_blocks": True,
                "lstrip_blocks": True,
                "extensions": self.settings["JINJA_EXTENSIONS"],
            }
        self.env = Environment(loader=ChoiceLoader(loaders), **jinja_environment)
        if "JINJA_FILTERS" in self.settings:
            self.env.filters.update(self.settings["JINJA_FILTERS"])
        if "JINJA_GLOBALS" in self.settings:
            self.env.globals.update(self.settings["JINJA_GLOBALS"])
        if "JINJA_TEST" in self.settings:
            self.env.tests.update(self.settings["JINJA_TESTS"])

    def read(self, source_path):
        with pelican_open(source_path) as text:
            text = self.env.from_string(text).render()

        with NamedTemporaryFile(delete=False) as f:
            f.write(text.encode())
            f.close()
            content, metadata = super().read(f.name)

            # Buggy Server customisation: make headlines "toc" links
            content = re.sub(
                JinjaContentMixin.HEADING_LINK_RE,
                JinjaContentMixin._enhance_heading, 
                content
            )

            os.unlink(f.name)
            return content, metadata


class JinjaMarkdownReader(JinjaContentMixin, MarkdownReader):
    pass


class JinjaRstReader(JinjaContentMixin, RstReader):
    pass


class JinjaHTMLReader(JinjaContentMixin, HTMLReader):
    pass


def add_reader(readers):
    for Reader in [JinjaMarkdownReader, JinjaRstReader, JinjaHTMLReader]:
        for ext in Reader.file_extensions:
            readers.reader_classes[ext] = Reader


def register():
    signals.readers_init.connect(add_reader)
