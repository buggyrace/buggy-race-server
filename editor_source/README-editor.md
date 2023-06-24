buggy-race-editor is a copy of the contents of
https://github.com/buggyrace/buggy-race-editor

If you change these files, remember to update
MANUAL_EDITOR_COMMIT in config.py
to indicate which commit these files were snapshotted from.

If you configure the race server to distribute this editor code (as a zip file)
instead of using GitHub, this is the source code it uses. This would be better
implemented using a git submodule, but — since the editor code changes
relatively infrequently — it's simpler to just have a manual copy here, and
doesn't require you to use github submodule commands (e.g., when cloning the
server).

If you use GitHub to distribute the code to the students, this copy will never
be used anyway.

Otherwise, it's used to produce the contents of the editor zipfile (after the
README has been customised).
