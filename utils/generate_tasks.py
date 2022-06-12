import re
import json
import markdown # utils needs Markdown (but production server doesn't)
import csv
from environs import Env
from collections import defaultdict

TASK_SOURCE='project/tasks.md'
OUTPUT_ISSUES = 'project/issues.csv'
ESCAPE_NEWLINES_IN_CSV = True

PROJECT_TEMPLATES = [
  'docs/project/tasks/index.md',
  'docs/project/poster.md',
]

env = Env()
env.read_env()

editor_repo_url=env.str("BUGGY_EDITOR_GITHUB_URL")
server_url = env.str("BUGGY_RACE_SERVER_URL")
server_project_path = env.str("SERVER_PROJECT_PAGE_PATH")
github_pages_url = env.str("GITHUB_PAGES_URL")
if not github_pages_url.endswith("/"):
  github_pages_url += "/"
project_task_pages_url = github_pages_url + "project/tasks/"

print("[ ] reading tasks from {}:".format(TASK_SOURCE))

# custom_tidy for Markdown going into CSV for GitHub
def custom_tidy(in_str):
  if ESCAPE_NEWLINES_IN_CSV:
    in_str = in_str.replace("\n", "\\n")
  return in_str

tasks = []

file_in = open(TASK_SOURCE, "r", encoding="utf-8")
task = {}
line = file_in.readline()
i = 0 # print("--{} {}".format(i, line))
while line:
    h1 = re.findall(r"^#\s+((\d)-\S+)", line)
    h2 = re.findall(r"^##\s+(.*)", line)
    h3 = re.findall(r"^###\s+(\w+)", line)
    if len(h1)==1:
        task['id'] = h1[0][0] # print("------- found: " + h1[0][0])
        task['phase'] = h1[0][1]
    elif len(h2)==1:
        task['title'] = h2[0].strip()
    elif len(h3)==1:
        section_name = h3[0].lower()
        section_lines = []
        end_of_task = False
        line = file_in.readline()
        i += 1 # print("-+{} {}".format(i, line))
        while line and not end_of_task:
            h3 = re.findall(r"^###\s+(\w+)", line)
            if not line.startswith("#"):
                section_lines.append(line.strip())
                line = file_in.readline()
                i += 1 # print("++{} {}".format(i, line))
            else: # end of a section
                task[section_name] = "\n".join(section_lines).strip()
                desc_lines = []
                if len(h3)==1: # new section
                    section_name = h3[0].lower()
                    section_lines = []
                    line = file_in.readline()
                else:
                  end_of_task = True
        tasks.append(task)
        print("[ ]   task: " + task.get('id', "<missing!>"))
        task = {}
        continue # already read
    line = file_in.readline()
    i += 1

file_in.close()

csvfile = open(OUTPUT_ISSUES, 'w', newline='')
sep = "\n\n"
issue_writer = csv.writer(csvfile)
for task in tasks:
  link = "[{} full details]({}#task-{})".format(
            task['id'], project_task_pages_url, task['id'].lower()
          )
  issue_writer.writerow([
    "{} {}".format(task['id'], task['title']),
    custom_tidy(sep.join([task['problem'], task['solution'], link]))
  ])
csvfile.close()
print("[>] OK: wrote {} tasks to {} for GitHub".format(len(tasks), OUTPUT_ISSUES))
print("[ ] check these URLs look correct:")
print("[ ]   editor repo:  {}".format(editor_repo_url))
print("[ ]   project page: {}#task-{}".format(project_task_pages_url, "7-DEMO"))

print("[ ] now preparing HTML...")

tasks_by_phase = defaultdict(list)
for task in tasks:
  tasks_by_phase[task['phase']].append(task)

index_html=""
html=""
for phase in tasks_by_phase:
  index_html += "<h3>Phase {} tasks</h3>\n<ul>\n".format(phase)
  phase_index_html = phase_html = ""
  for task in tasks_by_phase[phase]:
      phase_index_html += """
<li>
  <a href="#task-{id_low}"><span>{id_hi}</span> {title}</a>
</li>""".format(
        id_low=task['id'].lower(),
        id_hi=task['id'],
        title=task['title']
      )
    
      hints = ""
      if 'hints' in task:
        hints = """
              <div class="item hints">
                {hints}
              </div>""".format(hints=markdown.markdown(task['hints']))
      phase_html += """
            <div class="task" id="task-{id_low}">
              <h3>
                <a href="#task-{id_low}">{id_hi}</a>
                {title}
              </h3>
              <div class="item problem">
                {problem}
              </div>
              <div class="item solution">
                {solution}
              </div>
              {hints}
            </div>
  """.format(
      id_low=task['id'].lower(),
      id_hi=task['id'],
      title=task['title'],
      problem=markdown.markdown(task['problem']),
      solution=markdown.markdown(task['solution']),
      hints=hints
  )
  html += """
  <div class="task-breakdown">
    <section class="phase-{phase}">
      <h2>
        Phase {phase} tasks
      </h2>
      {phase_html}
    </section>
  </div>
  """.format(
    phase=phase,
    phase_html=phase_html
  )
  index_html += phase_index_html + "</ul>"

# squash leading spaces because we're done with them now
html = re.sub(re.compile(r"^\s*",re.MULTILINE), "", html)

# ...but report if somehow that's doubled up
if re.findall(r'\{\{ site\.site\.', html):
  print("[!]   found \{\{ site.site...\}\} duplication: check Jekyll vars")
  
re.MULTILINE

print("[ ] checking lines for Jekyll var substitution errors...")
qty_errors = 0
for line_count, line in enumerate(html.split("\n")):
  jekyll_subs = re.findall(r'\{\{\s*([.a-z]+)', line)
  for jekyll_sub in jekyll_subs:
    if jekyll_sub.startswith("site.site.") or not jekyll_sub.startswith("site."):
      print("[!]  line {}: \{\{{}\}\}".format(line_count, jekyll_sub))
      qty_errors += 1
line_count += 1 # because index started at 0
if qty_errors:
  print("[!] error! found {} in {} lines".format(qty_errors, line_count))
else:
  print("[ ] OK: found no Jekyll sub problems in {} lines".format(line_count))

poster_task_html = ""
for task in tasks:
  poster_task_html += """
```html
<div class="task">
  <h2>{} {}</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```
""".format(task['id'],task['title'])

for project_template in PROJECT_TEMPLATES:

  print("[ ] reading project template {}...".format(project_template))

  template_html = ""
  template_file = open(project_template, "r", encoding="utf-8")
  qty_lines = 0
  for line in template_file:
    template_html += line
    qty_lines += 1
  template_file.close()
  print("[ ] OK: read {} lines".format(qty_lines))

  template_html = re.sub(
    re.compile(
      r"(<!--\s*=*\s*PHASE-INDEX-START\s*=*\s*-->).*(<!--\s*=*\s*PHASE-INDEX-END\s*=*\s*-->)\s*",
      re.MULTILINE|re.DOTALL
    ), r"\g<1>\n" + index_html + "\n\g<2>\n", template_html
  )

  template_html = re.sub(
    re.compile(
      r"(<!--\s*=*\s*TASK-LIST-START\s*=*\s*-->).*(<!--\s*=*\s*TASK-LIST-END\s*=*\s*-->)\s*",
      re.MULTILINE|re.DOTALL
    ), r"\g<1>\n" + html + "\n\g<2>\n", template_html
  )

  template_html = re.sub(
    re.compile(
      r"(<!--\s*=*\s*POSTER-TASK-HTML-START\s*=*\s*-->).*(<!--\s*=*\s*POSTER-TASK-HTML-END\s*=*\s*-->)\s*",
      re.MULTILINE|re.DOTALL
    ), r"\g<1>\n" + poster_task_html + "\n\g<2>\n", template_html
  )

  template_file = open(project_template, "w", encoding="utf-8")
  template_file.write(template_html)
  template_file.close()

  print("[>] updated project template OK")

print("[ ] done: files × {} — remember to check and commit {}".format(
  len(PROJECT_TEMPLATES),
  "it" if len(PROJECT_TEMPLATES) == 1 else "them"
))
