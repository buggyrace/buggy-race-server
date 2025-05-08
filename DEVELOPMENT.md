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


## Smoke test: bare bones, just see it running

If you just want to spin the race server up as a local dev smoke test, the
following are the bare bones that should get you going (Unix/MacOS). If you've
got time to be more thorough, don't use this: step through the more detailed
instructions in the rest of this document instead.

Bare bones, from the the top directory of the `buggy-race-server` repo: this
runs a race server on `localhost:5000` with an empty SQLite database (you'll
need the default auth code: `CHANGEME`):

> Note: you can skip the two `export`s here by creating a `.env` file instead:
> do `cp env.example .env` and then edit `.env`. See notes below!

```bash
$> npm install
$> webpack
$> python -m venv venv
$> source venv/bin/activate
$> python -m pip install -r requirements.txt
$> export DATABASE_URL=sqlite:////tmp/buggy.db
$> export FLASK_APP=buggy_race_server/app.py
$> flask db upgrade
$> flask run
```

Ctl-C stops the webserver and `deactivate` exits the virtual environment.


## Getting started

The following notes are for a manual set-up. If you're familiar with docker
maybe you just need to do `docker-compose up`.


### Node for webpack

Currently we've still got the dependency on webpack, and hence node. Get this
out of the way first.

    npm install


## Set up Python

Although it probably still runs with older Pythons, currently we're running it
with Python 3.12.

Set up a virtual environment with:

    python -m venv venv

then do `source venv/bin/activate` (later... `deactivate` to stop it).

Get the libraries/modules:

    pip install -r requirements.txt

> _J:_ Requires gevent which sometimes needs special treatment on MacOS.
> Specifically, if homebrew is used to install stuff then it may have installed
> some header files (`/usr/local/header/uuid/uuid.h`) from `util-linux`. I had
> to remove them to get gevent to compile.

> _D:_ Earlier I bumped into problems with `psycopg2-binary` breaking the pip
> install on MacOS (it seems to behave recently though) —  a workaround was
> removing it from the requirements and falling through to a system one that was
> already installed; good luck. If you are totally blocking on this, a panic
> bypass is to switch to mySQL or SQLite ;-)


## Flask needs to know where the app is!

By default, flask looks for `app.py` in the current directory. Unfortunately,
the Race Server's `app.py` isn't in the project's root directory (there are
good reasons for this, inherited from `flask-cookiecutter`) so you need to tell
it: either set the environment variable `FLASK_APP` to be
`buggy_race_server/app.py`:

    export FLASK_APP=buggy_race_server/app.py

or use the `app` option when you run `flask`:

    flask --app=buggy_race_server/app.py

or declare the env variable with each invocation:

    FLASK_APP=buggy_race_server/app.py flask

or (maybe the best option because do-it-once now and you're good thereafter):

    cp env.example .env

...and then edit that `.env` file! (It's got `FLASK_APP` in it already).


### Set up a database

> _There are SQL-dialect specific notes further down in this file!_

You must explicitly tell the race sever which database to use with the
`DATABASE_URL` environment variable.

> If you want to use mySQL or PostgreSQL then you need to get those services up
> and running first, which is beyond the scope of this document, and you'll
> need to create a database to use. When you've done that you need to nominate
> it in the `DATABASE_URL` environment variable: for that you'll probably need
> to know the database name, the port it's server from, the username of the
> owner and their password.
>
> Alternatively, provided this is just for dev/smoke test, you can use
> SQLite instead: it doesn't need to run as a service.

Probably the most convenient way set `DATABASE_URL` is to use a `.env` file,
because your flask app will look in there. If you don't have one already,
copy `env.example` to `.env` and edit it. You'll see example values there for
databases, including the SQLite one. If you use SQLite you don't even need to
create the database first, because running the app will create it (although
note you'll still need to populate it with the `flask db` command).

We've been using `flask db` to manage the database, but note that flask won't
recognise the `db` command if you haven't told it where the app is (see the
previous section — for example, export `FLASK_APP` or set it in `.env`):

    flask db upgrade

(this applies the migrations and creates the tables, etc).


### Set up environment variables

The critical ones are `FLASK_APP` and `DATABASE_URL`. The easiest way to set
things up is

    cp env.example .env

...and edit that. Set or use the default value for `AUTHORISATION_CODE` (you
will need it to do anything useful within the admin interface).

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


### Run webpack (to make the static asset "bundles")

The webserver uses webpack to gather all the CSS, Javascript, and images into
a `static/build/` directory. If you're not changing any of those things, you
only need to run this once. Unfortunately webpack uses node, so you'll need to
install that and all its libraries too:

    npm install

...that creates `node_modules` loaded with all the libraries and dependencies.
Then run webpack with something like:

    webpack

or (`npm run webpack-watch` with a Ctl-C when it's done).


### Run the webserver

The simplest, dev-only way of doing this is:

    flask run

That will only work if the environment variables are available to it — which
they should be if you've got here by following the previous set-up. 

Because you're starting with an empty database, the race server will be in
set-up mode when you first launch — you'll be guided through a bunch of config
screens (most of which you can accept the defaults for: see the full
documentation at https://www.buggyrace.net/docs/ because at this point you're
inside the application).


#### Other ways to run it

If you want to run the webserver directly, the command that npm is
launching (you can see this in `package.json`) is:

    gunicorn buggy_race_server.app:app -b 0.0.0.0:8000 -w 1

Alternatively, you can try to run the same way it happens up on heroku, by
telling node to launch things:

    npm start

which will run both webpack and the flask app: however note that this will
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

If you get `Error: No such command 'db'` it's because you've not told flask
where its app is either with  the `FLASK_APP` environment variable or the
`--app` option.


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


### How to load a database restore into a local (postgres) database

The `pg_restore` command will take a dump you've saved (e.g., from Heroku) and
restore a database — it contains a few things that aren't relevant in your local
copy (such as a `OWNER` information). Assuming you've already created a database
(it's presumably what you've been developing with) you can replace it with the
contents of the dump file like this:

    pg_restore --clean -O -d database_name latest.dump

`--clean` wipes the existing database (called `database_name`), `-O` uses the
current postgres user as the `OWNER` and ignores what is in the dump, and
`latest.dump` is the name of the Postgres dump file you got from doing `pg_dump`.


### How to add a new config setting to the code

Adding a new config setting is relatively straightforward provided you add
_everything_ in this list at once. You _must_ provide a default value for the
setting: the first time the code is run, the new setting will be added to the
database and it will use this value if (as is likely in existing installations)
there's no explicit value provided in ENV or `.env`.

Go to `buggy_race_server/config.py` and add the new setting there. It's a good
idea to find the most similar existing setting and search for that, because this
is really about following the existing pattern!

* Add the setting to the `ConfigSettingNames` `enum`. If it's one that admin
  should edit during setup, add it to the (long) list that appears after
  the comment "User-editable config settings: presented in the settings/config"

* If it's a setting that admin should edit during setup, add it to the 
  relevant `GROUP` in `ConfigSettings`

* Add its default value to `DEFAULTS` in `ConfigSettings`.
  You **must** add a default because this setting will be added (i.e., written
  to the database) when the app launches.

* Add the correct type to `TYPES` in `ConfigSettings`. If you don't it will
  default to `STRING`... but be explicit anyway, so there's no doubt you meant
  it to be what it is.

* If it's a setting that admin should edit during setup, add a helpful text to
 `DESCRIPTIONS`. This is used both in the config-setting form and also in the
 documentation: see _How to keep the customising pages up to date in the docs_
 below for the semi-automated way this works.

If you do those things, the next time you run the race server app you'll see
(in the console) a message telling you a config setting (with default value)
was inserted into the database.


### How to remove a config setting from the code

If you made a config setting obsolete, that is, you _remove_ it from `config.py`
because it's no longer used, the redundant setting will persist in the database
_but_ a friendly blue button appears on the admin dashboard inviting you (or any
staff user) to "purge" it. That's a safety mechanism which might be handy during
development.

Be sure to remove all references to it, of course — so you'll pretty much be
doing the opposite of the process for adding a new setting to `congig.py`, above.


### How to change a model and its underlying database table

This is managed via Flask/SQLalchemy's ORM. If you add or change a model (for
example, to add a `star_sign` attribute to `User`, you'd edit the class in
`user/models.py`) and then run Flask's `db migrate`:

    flask db migrate -m "store user's star sign"

This will produce an migration file. You'll need to apply it with
`flask db upgrade` in order to make changes to the database. Those migrations
are run automatically as part of the deploy mechanism on heroku for example,
which is how live installations' databases get migrated to match the code
they are being deployed with. If we get an accumulation of migration files,
there comes a point when it's tidier to delete them all and make a new
single one, but this is a breaking change and would have to be a new version
release of the whole server. Note that you should also make no-data dump of
the latest database and save it as a new commit on `schema.sql`. This is a 
convenience that allows anyone who can't run the migrations to still set up
their database.

_Note for devs:_  
Behind the scenes this is Flask-SQLalchemy doing a pretty impressive job of
generating the schema migrations _but_ we have bumped into some SQL-dialect
gotchas (some ALTER TABLE column changes break in SQLite, although mySQL and
Postgres handle indexes a little differently too). Before you push any code
back, as a courtesy please check you haven't broken the migrations for the
dialect you're _not_ using, because this is a blocker for other devs who hit it
later.


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

Go to `/admin/config-docs-helper` in any current install of the server that
has `_IS_DOCS_HELPER_PAGE_ENABLED` set to `1` (i.e., is set to be truthy).
That gives you the markdown for the config settings section (including their
default values) ready to be copy-and-pasteed into the relevant part of the page.
This takes a bit of time because you really do need to do it page-by-page unless
you're sure you know which specific page has changed (e.g., if you've just
added one new config setting). Alternatively, there's a utility script in
the docs repo (`buggy-race-about`) that takes the downloaded text file from
that docs helper and replaces _all_ of the customisation pages with the tables
of settings values. It also passes the current (suspected; it's not clever)
version string and updates that in the docs too.


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

This icomoon process (of re-constituting the font by picking all the symbols
we are using) is getting cumulatively more fiddly as we add more and more icons,
hmm.


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
bumped to `v2`: this was a breaking change. There were more breaking changes
(in the config setting handling, I think) in 2024 which is why we bumped up
to `v3`.



