Title: index


# {{ PROJECT_CODE }} Tech notes

Notes to explain how to do (and understand) project tasks.

## Especially for phase 0

For task [0-GET: Get the source code]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-0-get):

* [about forking (and cloning) the repo](forking-the-repo)

For task [0-RUN]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-0-run):

* [using localhost](localhost) (or: why isn't 0.0.0.0 working?)

## Things that are useful from the start

Your buggy editor is a webserver... 

* [what is a webserver?](webserver)
* ...then: [how Flask works as a webserver](flask-webserver)

Debugging tips:

* [use print()](print-debug)
* [“error in update operation”](error-in-update) or problems saving to the
  database

General set-up:

* [how to set FLASK_ENV](setting-env)

Adding comments to your code:

* [comments](comments) in Python and HTML... and more

## Especially for phase 1

Notes for task
[1-TEMPLATE: Add a new template to the app]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-template):

* [templates in Flask](jinja-templates) (where the HTML comes from)
* [routes in Flask](routes-in-flask) (how it picks the right template)


Notes for task
[1-ADD: Add more data to the form]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add):

* [identify the template to edit](identify-template)
* [add input tag to the form](add-input-to-form)
* [handle the POST request](handle-post)
* [know what's in the database](database-structure)
* [add new data: CREATE TABLE](adding-new-data-i)
* [add new data: ALTER TABLE](adding-new-data-ii)


## More general things for once you've got going

Notes to overcome CSS not changing when you hit _refresh_
(may help with [1-STYLE]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-style)):

* [static vs. dynamic](static-vs-dynamic)
* [cache-busting the CSS](cache-busting-css)

Notes for using Flask's _flash messages_:

* [setting a secret key](secret-key) (also: how cookies work)
* [flash messages](flash-message)

How to add images to your Flask app:

* [adding static content](static-content)


