# find all headings and wrap them with anchor tags

import re
import sys

slug_lookup = {}

def slugify(string):
  # replace all non-slug chars with -
  # top, trail, compress -s
  # *BUT* leave {{ arbitary code }} in!
  sluggables = re.split(r"({{[^}]*}})", string)
  slug_list = []
  for slug_part in sluggables:
      if slug_part.startswith("{{") and slug_part.endswith("}}"):
          slug_list.append(slug_part)
      else:
          slug_part = re.sub(r"[^a-z0-9]+", "-", slug_part.strip().lower())
          slug_part = re.sub(r"(^-+|-+$)", "", slug_part)
          slug_part = re.sub(r"--+", "-", slug_part)
          slug_list.append(slug_part)
  slug = re.sub(r"(^-+|-+$)", "", "-".join(slug_list))
  if slug in slug_lookup:
      count = slug_lookup[slug]
      slug_lookup[slug] += 1
      slug = f"{slug}-{count}"
  else:
      slug_lookup[slug] = 1
  return slug

if len(sys.argv) != 3:
  print(f"Usage: {sys.argv[0]} input_html_file output_file")
  quit()

input_filename = sys.argv[1]
output_filename = sys.argv[2]

html = ""
with open(input_filename) as infile:
    html = "".join(infile.readlines())

print(f"html={len(html)}")
HEADING_RE = re.compile(r"<h(\d)(\s*[^>]*)>(.{1,80})</h\1>")
CLASS_RE = re.compile(r"(class\s*=\s*([\"']))(.*?)(\2)")
ID_RE = re.compile(r"(id\s*=\s*([\"'])(.*?)(\2))")
ANCHOR_CLASS = "toclink"

new_html = ""

slug_lookup = {}

while matched := re.search(HEADING_RE, html):
    start = matched.start()
    end = matched.end()
    new_html += html[:start]
    hx = matched.group(1)
    attribs = matched.group(2)
    text = matched.group(3)
    slug = slugify(text)
    if id_match := re.search(ID_RE, attribs):
        id = id_match.group(3)
        attribs = attribs.replace(id_match.group(1), "")
        if id != slug: # report if we're not replacing like with like
          print(f"[ ] heading (h{hx}) already had id=\"{id}\", replacing with {slug}")
    attribs += f" id=\"{slug}\""
    new_html += f"<a href=\"#{slug}\" class=\"toclink\"><h{hx}{attribs}>{text}</h{hx}></a>"
    html = html[end:]
new_html += html

with open(output_filename, "w") as outfile:
    outfile.write(new_html)

print(f"[ ] wrote {len(new_html)} chars to {output_filename}")
print(f"[ ] done: added {len(slug_lookup)} anchors/slugged ids")

