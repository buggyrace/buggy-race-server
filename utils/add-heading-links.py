# find all headings and wrap them with anchor tags

from bs4 import BeautifulSoup
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

raw_html = ""
with open(input_filename) as infile:
    raw_html = "".join(infile.readlines())

HEADING_RE = re.compile(r"<h(\d)(\s*[^>]*)>(.{1,80})</h\1>")
CLASS_RE = re.compile(r"(class\s*=\s*([\"']))(.*?)(\2)")
ID_RE = re.compile(r"(id\s*=\s*([\"'])(.*?)(\2))")
ANCHOR_CLASS = "toclink"

new_html = ""

slug_lookup = {}

soup = BeautifulSoup(raw_html, 'html.parser')

# if there's an anchor tag wrapped around a header,
# this may be an anomoly: fix it by removing the <a> tags completely
# (on the assumption we're about to rebuild them inside the header)
for anchor in soup("a"):
    for h_level in range(1, 7):
        if heading := anchor.find(f"h{h_level}"):
            print(f"Found an anchor around a h{h_level}, removing it")
            anchor.replaceWith(heading)

for h_level in range(1, 7):
  for heading in soup.find_all(f"h{h_level}"):
      if inner_link := heading.find("a"):
        print(f"    found an anchor inside h{h_level}: {inner_link['href']} FIXME TODO")
      heading_text = heading.text
      slug = slugify(heading_text)
      print(f"h{h_level}: {heading.text}")
      id = heading.get("id")
      if id and id != slug:
           print(f"[ ] heading (h{h_level}) already had id=\"{id}\", replacing with {slug}")
      heading["id"] = slug
      new_anchor = soup.new_tag("a", href=f"#{slug}")
      new_anchor["class"]=ANCHOR_CLASS
      new_anchor.string = heading_text
      heading.string = ""
      heading.append(new_anchor)

with open(output_filename, "w") as outfile:
     outfile.write(soup.prettify())

# print(f"[ ] wrote {len(new_html)} chars to {output_filename}")
# print(f"[ ] done: added {len(slug_lookup)} anchors/slugged ids")

