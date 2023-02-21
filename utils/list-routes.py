import re
from subprocess import run

# lists the (sorted) routes for the Flask app by inspecting Bluetooth
# route definitions

PREFIX_RE = re.compile(r"Blueprint\(\s*['\"](\w+)['\"][^\)]*(url_prefix=['\"]/([^'\"]+))")
grep_output = run(["git", "grep", "Blueprint("], capture_output=True)
prefixes = {}
for match in re.findall(PREFIX_RE, str(grep_output.stdout)):
    (module, prefix) = match[0], match[2]
    prefixes[module] = prefix

ROUTE_RE = re.compile(r"buggy_race_server/(\w+)/views.py:\@blueprint.route\((['\"])/?(.*?)/?\2")
grep_output = run(["git", "grep", "blueprint.route"], capture_output=True)

routes = []
for match in re.findall(ROUTE_RE, str(grep_output.stdout)):
    (module, path) = match[0], match[2]
    if module == "public":
        prefix = ""
    else:
        prefix = "/" + (prefixes.get(module) or module)
    routes.append(f"{prefix}/{path}")

routes.sort()
print("\n".join(routes))
