# Installation notes

> See [https://www.buggyrace.net/docs/](https://www.buggyrace.net/docs/)
> for full documentation for the buggy racing project.

## Background

This app started out as a
[cookiecutter-flask](https://github.com/cookiecutter-flask/cookiecutter-flask).
which means its structure was inherited from that.


---

## Local "manual" installation:

If you want to run a local installation to play with it, see the developers'
notes in `DEVELOPMENT.md`

The bare-default setup will run the buggy-racing server website locally on
port 5000: hit it in a browser on [http://localhost:5000/](http://localhost:5000/)
using an SQLite database (not suitable for production! — see the development
notes for using PostgreSQL or mySQL).

When the server first runs, it's in setup mode. You will be invited to change
the authorisation code (which by default is `CHANGEME`), an admin username, and
an admin password.

Once you've submitted that, you'll be logged in as that admin user, and you'll
be guided through the setup. You must complete this process before the server
is ready — it takes a few minutes. Most of the settings have sensible defaults.


