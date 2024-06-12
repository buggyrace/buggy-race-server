# buggy-race-server development

These notes are combined from Dave and Jasper's notes for running a dev
environment.

> Note that there are _detailed_ docs at
> [https://www.buggyrace.net/docs/](https://www.buggyrace.net/docs/)
> — those aren't for devs but they are definitive for what is supposed to
> happen when you run the app.
>
> The three repos:
>
> * https://github.com/buggyrace/buggy-race-server
> * https://github.com/buggyrace/buggy-race-editor
> * https://github.com/buggyrace/buggy-race-about


## Getting started

The following notes are for a manual set-up. If you're familiar with docker
maybe you just need to do `docker-compose up`.


### Node for webpack

Currently we've still got the dependency on webpack, and hence node. Get this
out of the way first.

    npm install


## Set up Python

Use Python 3.9+ (3.8 works but timezones came into the standard library in 3.9
and although we're not using that yet, we're almost certainly going to).

Set up a virtual environment with

    python -m venv venv

then do `source venv/bin/activate` (later... `deactivate` to stop it).

Get the libraries/modules:

    pip install -r requirements.txt

> _J:_ Requires gevent which sometimes needs special treatment on MacOS.
> Specifically, if homebrew is used to install stuff then it may have installed
> some header files (`/usr/local/header/uuid/uuid.h`) from `util-linux`. I had
> to remove them to get gevent to compile.

> _D:_ I've bumped into problems with `psycopg2-binary` breaking the pip
> install on MacOS —  a workaround was removing it from the requirements and
> falling through to a system one that was already installed; good luck. If
> you are totally blocking on this, a panic bypass is to switch to mySQL ;-)


### Set up a database

> _There are SQL-dialect specific notes further down in this file!_

If you don't explicitly set a database, the default is an SQLite one — but if
you've got mySQL or PostgreSQL running then it's best to use that: create a
database by saying something like this to your SQL shell:

    CREATE DATABASE buggyrace

...and make sure you know the username of the `OWNER` and their password,
because you need that in the `DATABASE_URL`.

We've been using `flask db` to manage the datbase, but note that it needs to
find the flask app, so you might need to set `FLASK_APP` first, e.g.:

    export FLASK_APP=buggy_race_server/app.py

Populate the database with:

    flask db upgrade

(this applies the migrations and creates the tables, etc).

If you change the models and want to create new migrations, do something like:

    flask db migrate -m "store user star sign"

Behind the scenes that's Flask-SQLalchemy doing a pretty impressive job of
generating the schema migrations _but_ we have bumped into some SQL-dialect
gotchas (some ALTER TABLE column changes break in SQLite, but mySQL and
Postgres handle indexes a little differently too). As a courtesy please check
you haven't broken the migrations for the dialect you're _not_ using, because
this is a blocker for other devs who hit it later.


### Set up environment variables

Unless you're using the default SQLite database, the critical one is
`DATABASE_URL`. The easiest way to set things up is

    cp env.example .env

...and edit that. Set or use the default value for `AUTHORISATION_CODE` (you
will need it to do anything useful within the admin interface).

You need to have `FLASK_APP` set too — `buggy_race_server/app.py` works (which
is the default).

Almost all the config settings for buggy racing are stored in the database, but
the app reads the environment variables first, and _overwrites_ any it finds
which are known buggy racing settings by writing them into the database on
start-up... and _then_ reading them all out of the database. This means you can
force any setting by e.g. editing `.env` and restarting the server. See [the
docs about this](https://www.buggyrace.net/docs/customising/env.html)

The general policy for config is anything that's handy in Flask's `config`
should be coming via the database. That's why there are a load of settings that
are prefixed with `_` which are effectively application constants. These aren't
exposed in the web interface for changing config settings (i.e., buggy racing
admins can't change them without diving into the env backstage). If it's
useful, have a look at `/admin/system` which dumps a load of them for you.


### Run the webserver

We had different ways of doing this, but you could try:

    npm start

will try to run both webpack and the flask app: however note that this will
run webpack (once) and launch the webserver on a secure connection — if you're
running on localhost check you're hitting **secure `localhost`**
([https://localhost:5000](https://localhost:5000)) because `http` and
`0.0.0.0` won't work.

> Note there is a 15 second delay before the web server kicks in: this is to
> allow the database migrations to run before the app runs when starting up
> in steups like Heroku and Docker (this matters because the app looks in the
> database for config when it launches).

But as you're trying to run the app as a developer, you might want to run
things separately:

* `npm run webpack-watch`  
  run webpack and have it listen for changes.

* `npm run flask-server-dev`
  to run flask webserver without the  15 second delay and without SSL
  — then you can hit [http://localhost:5000](http://localhost:5000)


If you want to run the webserver directly, the command that npm is
launching (you can see this in `package.json`) is:

    gunicorn buggy_race_server.app:app -b 0.0.0.0:8000 -w 1


### Common new install error: static files give 403

If you haven't run `webpack` (which requires node, so do `npm start`), the
static resources don't exist but Flask won't look, so you get an unstyled
response from the server with the CSS, JS and images giving a `403` instead of
`404`. Run webpack once (or keep it running in listening mode if you're
changing static stuff) to populate those assets.

If webpack won't run (sigh) because something something run-script-os, you
might need to do

    npm install --save-dev run-script-os


### How to set up the database on a new install

`flask db update` should run the migrations, so you end up with the right
tables in the database. But for convenience we try to keep `db/schema.sql`
up-to-date: that's a SQL dump of the structure of the database, so you can run
that to initialise the tables (etc) _instead_ of migrations. Ideally you don't
do it this way because the migrations are likely to always be the definitive
way to do it. But this gives you a way to get the database up and running
separately from Flask and the app and/or if you're using a dialect of SQL that
chokes on a migration (if you hit this, let us know).


### How to connect to SQLite (dev only!)

The env variable needs to be something like (which is cheekily our default in
the example environment file):

    DATABASE_URL=sqlite:////tmp/buggy-race-server.db


### How to connect to mySQL

mySQL gets through with `mysql-connector-python` (`mysqldb` is no longer
supported). Use it like this:

    DATABASE_URL=mysql+mysqlconnector://username:password@localhost:8889/databasename


### How to connect to PostgreSQL

PostgreSQL is our production db of choice — here's what the URL looks like:

    DATABASE_URL=postgres://username:password@host:port/dbname

(note Heroku uses port 5432 and generates this whole string for you).

Heads up that if you try to connect to mySQL credentials with the `postgres`
scheme, you get this cryptic error:

    psycopg2.OperationalError: received invalid response to SSL negotiation: J

Oops.


### How to dump data from postgres running on Heroku

There's more than one way of doing this but the convenience of the Heroku CLI
makes this handy: _within_ psql you can issue a local command with `\!`.

You might need to force the pg_dump version to match Heroku's PostgreSQL version
but I got round that with an explicit (versioned) path in the command: for example
this dumps _just the data_ (handy for reloading the demo site?):

    \! /Library/PostgreSQL/15/bin/pg_dump --column-inserts --data-only DATABASE_NAME > example.sql

The options `--column-inserts` `--data-only` force this to be a data-inserting-only
SQL file. You can also use `--table=users` for example.

### How to add animated diagrams to the Tech Notes (202)

> There are currently two: in _webserver_ and _flask-webserver_:
> (`/tech-notes/contnet/tech-notes/*.md`)

The SVG diagrams are made with [KeyShape](https://www.keyshapeapp.com) (Mac
only) and then made interactive with the
[KeyshapeDiagram script](https://github.com/davewhiteland/keyshape-diagram)
([docs](https://davewhiteland.github.io/keyshape-diagram/docs)),
which was written for the SuperBasics project.

* in KeyShape, add _named time markers_ to the diagram
* export as SVG with these settings:
  * Format: **SVG**
  * Animation: **KeyshapeJS Animation**
    * _do not write SVG1.1 filters_ (my diagrams probably haven't needed them
      anyway)
    * _do check all these:_ write text as paths, embed images, Optimize
      (defaults are OK)
  * Object IDs: **Prefix** `svg-01-` (probably doesn't matter)
  * JS Library: **External** (see below: you're pasting it into the page anyway)
  * Loops: **Play once**
* add a `<div class="example"></div>` to the markdown page in tech notes
* copy-and-paste the contents of the external `keyshapejs-1.2.0.min.js` script
  into a `<script>` tag inside the example div (unless it's being served as an
  external resource, which it isn't (yet) because the two tech_note diagrams
  are from different versions of KS)
* copy-and-paste the SVG the div as the `<svg>` element it already is...
* add `class="ksd"` to the that SVG!
* add the captions as `<ol class="ksd-captions">` (the order is critical (of
  course): match the timestamps in your animation... otherwise you _can_ do by
  matching IDs but I haven't needed to)
* add a no-JS fallback div too: `<div class="ksd-no-js">`
* finally remember to call `ksd.js` at the bottom of the page to make it happen


### How to keep the customising pages up to date in the docs

The docs about customising the race server include all the config settings and
descriptions which are from `config.py` within the application. For example, see
the page [about the server settings](https://www.buggyrace.net/docs/customising/server.html).

Go to `/admin/config-docs-helper` in any current install of the server to
get the markdown for the config settings (including their default values)
and copy-and-paste the section that's changed into relevant section of the page.

Note that some pages — specifcally the `auth` and `social` setting groups —
don't use the verbatim text (you'll see if you look inside them).


### How to run a race 

This used to require running within the Flask shell. That's been dropped and
for now this is simpler — running `utils/run-buggy-race.py` is enough, provided
the import of the `BuggySpecs` from `buggy_race_server.lib.race_specs` works.
That's OK for now but maybe there's a case for importing the buggy specs as
data.


### How to find all the routes

The server has an unlinked `/admin/routes` page that dumps them out for you.


### How to add a new icon to the icomoon font

We're using icons from the free icomoon pack (thanks icomoon!)

There are currently 14 icons in the custom incomoon font. Here's the manual
process you need to follow if you need to add a new one:

Go to [icomoon.io/app](https://icomoon.io/app/) and select all the icons you
need (to see which ones we're using, look inside
`buggy_race_server/assets/css/fonts/icomoon.svg` where you can see the names).

Select the icons you want and click on **Generate Font**. Be sure to include
_all_ the icons we're already using unless you are deliberately removing them!
(Also, note that you can use the iconmoon.io website's search bar to select
the icons by name!) The font files inside the zipfile can be copied into place
in `buggy_race_server/assets/css/fonts/`. Look in that `icomoon.svg` file to
get both the name and the character number for the new icon.

Then go to `buggy_race_server/assets/css/style.css` and add your new icon as
an `icon-` class, like this:

    .icon-trophy:before { content: "\e99e"; }

These are used like this:

    <span class="icon-trophy"></span>


### Workflow/hardcoded version number

We might tighten this up, but currently the `development` branch is where the
action happens (sometimes feature dev is done in a branch and merged in) — we
can revisit this if needed. (It's been a pragmatic rather than principled
decision just to get it all done).  When releases happen, the hard-coded
version number is bumped in `config.py` and then a pull request made and
squashed into `main`.

Finally (a bit naughty) we then pull `main` and merge it back into `development`
just to keep it simple for the next PR.

`main` should always be deployable, with a unique version number showing up
in the `/admin/system` (or `/about` under the hamster) pages.

We zeroed the migrations at the end of the (somewhat frantic) development that
was going on during RHUL term 3 in 2023, which is why the version number was
bumped to `v2`: this was a breaking change.



