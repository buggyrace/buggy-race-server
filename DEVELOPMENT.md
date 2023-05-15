# buggy-race-server Development

## Jasper's Notes:

### Getting started

1. `pip install -r requirements.txt`
    * Requires gevent which sometimes needs special treatment on macos. Specifically, if homebrew is used to install stuff then it may have installed some header files (`/usr/local/header/uuid/uuid.h`) from `util-linux`. I had to remove them to get gevent to compile.
2. `flask db init`
3. `flask db upgrade`
4. `flask db migrate`
5. `cp env.example .env`
  * add your name or a preferred username to `ADMIN_USERNAME`
  * set or use the default value for `AUTHORISATION_CODE`, you will need it for registering accounts.
6. `npm install`
7. Run the flask app
  6.1. `npm start`
    * Skips everything and does the front end build magic and starts the flask app.
  6.2. `flask run`
    * The flask app and other settings are defined in `.env`
  6.3. `npm run webpack-watch` 


## Dave's Notes

When running locally (on my mac) I'm now kicking the app off by

1. being in a local `venv` virtual environment that has all the requirements
2. `gunicorn buggy_race_server.app:app -b 0.0.0.0:8000 -w 1 --timeout 60`

To use `flask` tools, probably need to set `FLASK_APP` (because the default expects `app.py` to be in `.`, and it isn't):

    export FLASK_APP=buggy_race_server/app.py

(e.g., for `db` commands that follow)


### Oauth application

The OAuth Application registered on GitHub by owner `davewhiteland`
(currently organisations can't register apps):

* for RHUL: https://github.com/settings/applications/1613423

### Common new install error: static files give 403

If you haven't run `webpack` (which requires node, so do `npm start`),
the static resources don't exist but Flask won't look, so you get an
unstyed response from the server with the CSS, JS and images giving
a `403` instead of `404`. Run webpack once (or keep it running
in listening mode if you're changing static stuff) to populate
those assets.

If webpack won't run (sigh) because something something run-script-os, 
you might need to do 

    npm install --save-dev run-script-os

### How to set up the database on a new install

`flask update` should run the migrations, so you end up with the right
tables in the database. But for convenience we try to keep `db/schema.sql`
up-to-date: that's a SQL dump of the structure of the database, so you
can run that to initialise the tables (etc) _instead_ of migrations. Ideally
you don't do it this way because the migrations are likely to always be
the definitive way to do it. But this gives you a way to get the database
up and running separately from Flask and the app.

### How to connect to sqlite (in dev)

The env variable needs to be something like (which is cheekily our default in the example
environment file):

    DATABASE_URL=sqlite:////tmp/dev.db
    
... but (sigh) SQLAlchemy makes migrations that break in sqlite (something about `ALTER TABLE` or
`COLUMN`) so in the end I switched to using mySQL for local quick-and-dirty dev (see below).

### How to connect to mySQL

Turns out [`mysqldb` is no longer supported](https://stackoverflow.com/questions/53024891/modulenotfounderror-no-module-named-mysqldb).
The workaround is to use `mysql-connector-python` (which is now in the project's (Python/pip) requirements) and
something like this:

    DATABASE_URL=mysql+mysqlconnector://username:password@localhost:8889/databasename


### How to connect to postgres

For completeness — and it's our production db of choice — here's what the URL looks like for postgreSQL:

    DATABASE_URL=postgres://username:password@host:port/dbname

(e.g., Heroku uses port 5432 and generates this whole string for you).
If you try to connect to mySQL credentials with the `postgres` scheme, you get this cryptic error:

    psycopg2.OperationalError: received invalid response to SSL negotiation: J

Oops.

### How to add animated diagrams to the Tech Notes (202)

> There are currently two: in webserver and flask-webserver
> (`/tech-notes/contnet/tech-notes/*.md`)

The SVG diagrams are made with [KeyShape](https://www.keyshapeapp.com) (Mac only)
and then made interactive with the
[KeyshapeDiagram script](https://github.com/davewhiteland/keyshape-diagram)
([docs](https://davewhiteland.github.io/keyshape-diagram/docs))
(which was written for the SuperBasics project).

* in KeyShape, add _named time markers_ to the diagram
* export as SVG with these settings:
  * Format: **SVG**
  * Animation: **KeyshapeJS Animation**
    * _do not write SVG1.1 filters_ (my diagrams probably haven't needed them anyway)
    * _do check all these:_ write text as paths, embed images, Optimize (defaults are OK)
  * Object IDs: **Prefix** `svg-01-` (probably doesn't matter)
  * JS Library: **External** (see below: you're pasting it into the page anyway)
  * Loops: **Play once**
* add a `<div class="example"></div>` to the markdown page in tech notes
* copy-and-paste the contents of the external `keyshapejs-1.2.0.min.js` script into a `<script>`
  tag inside the example div (unless it's being served as an external resource, which it isn't (yet)
  because the two tech_note diagrams are from different versions of KS)
* copy-and-paste the SVG the div as the `<svg>` element it already is...
* add `class="ksd"` to the that SVG!
* add the captions as `<ol class="ksd-captions">` (the order is critical (of course): match the
  timestamps in your animation... otherwise you _can_ do by matching IDs but I haven't needed to)
* add a no-JS fallback div too: `<div class="ksd-no-js">`
* finally remember to call `ksd.js` at the bottom of the page to make it happen


### How to run a race 

This used to require running within the Flask shell. That's been dropped and
for now this is simpler — running `utils/run-buggy-race.py` is enough, provided
the import of the `BuggySpecs` from `buggy_race_server.lib.race_specs` works.
That's OK for now but maybe there's a case for importing the buggy specs as
data.

Running the race provides the necessary file for uploading results, but it
doesn't (yet) produce the event log that presumably would be required to
replay it.


