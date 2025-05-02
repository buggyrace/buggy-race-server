Dev notes re: `editor_source`
=============================

`buggy-race-editor` contains a copy of the contents of
https://github.com/buggyrace/buggy-race-editor

> If you change these files, remember to update
> `MANUAL_EDITOR_COMMIT` in config.py
> to indicate which commit these files were snapshotted from.
>
> That repo's history is itself something of an anomaly, because it always only
> has an "initial commit" — because we don't think students' forks should be
> polluted with the history of the development of the Buggy Racing project.
> (See https://github.com/davewhiteland/buggy-race-editor for a somewhat more
> honest/development history of code changes).


Why is there a copy of the editor code here?
--------------------------------------------

If you configure the race server to distribute this editor code (as a zip file)
instead of using GitHub, this is the source code it uses. This could perhaps be
better implemented using a git submodule, but — since the editor code changes
relatively infrequently — it's simpler to just have a manual copy here, and
doesn't require you to use github submodule commands (e.g., when cloning the
server).

If you use GitHub to distribute the code to the students, this copy will never
be used anyway.

Otherwise, it's only used to produce the contents of the editor zipfile.


Note that `buggy-race-editor/README.md` is _not_ used!
------------------------------------------------------

When the zip file is "published" (admin → Buggy editor → Publish) it's
overwritten with the customised one, which is rendered from this Jinja template:

    buggy_race_server/templates/admin/_buggy_editor_readme.txt

...so that template contains Jinja markup that drops current config settings'
values in there. Compare with how the publishing mechanism inserts config
setting values into `app.py` by explicitly searching for a match to replace
(using a regex). That is fragile, because it will break if the editor's `app.py`
changes and we forget to update the regex. This is why we use the Jinja template
to produce the customised README!
