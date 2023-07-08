# Default tasks in these task files

File `tasks.md` contains the text for all the tasks _except_ the first
two tasks - 0-GET and 0-RUN. These depend on the config settings of the
distribution method, and the names/keys of those are in
`buggy_race_server/admin/models.py` as `DistribMethods`.
The default is "zip".

See the docs on
[Buggy editor: distributing the code](http://localhost:4000/docs/buggy-editor/distributing-the-code).

The utils method create_default_task_markdown_file(distrib_method)
creates a new markdown file in the uploads directory by concatenating
the contents of the distribution-specific file (first two tasks of
phase 0) and the contents of `tasks.md` (all the remaining tasks).

