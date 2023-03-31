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


### How to connect to sqlite (in dev)

The env variable needs to be something like (which is cheekily our default in the example
environment file):

    DATABASE_URL=sqlite:////tmp/dev.db
    
... but (sigh) SQLAlchemy makes migrations that break in sqlite (something about `ALTER TABLE` or
`COLUMN`) so in the end I switched to using mySQL for local quick-and-dirty dev (see below).

Might be worth dumping a `dev.db` into the repo with the current schema and a default
admin user so just pointing DATABASE_URL to it could get going quickly (avoiding any `flask db`
setup that hits the migration problem). Currently there's a register-an-admin dance in dev that
this would bypass (Might only be handy for me cos I'm currently avoiding
using containers: possibly more useful to have a latest `dev.sql` to load up bypassing the migrations
entirely.

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


### How to run a race 

Here's how I ran the race, having cloned the repo:

    $ cd buggy-race-server

Set up a venv to keep things tidy

    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

Copy the local dev settings into `.env`

    $ cp env.example .env

Might not need this but belt and braces

    $ export FLASK_APP=autoapp.py

Make the (SQL database): upgrade basically makes it

    $ flask db upgrade

(You can also do `flask db migrate` — which is safe — to be
sure you've got any changes since, but if you've just cloned it
you'll see "No changes in schema detected")

Now go into the shell: the point is this give access
to all the app's models in a commandable shell, nice

    $ flask shell

You should see "App: buggy_race_server [development]".
Grab the buggy_race which (potentially) runs the races!

    $ import buggy_race

Load the CSV that you downloaded from the race server

    $ buggy_race.load_csv()

This starts by reading the buggies from the database, if
there are any. This is because Flask uses an ORM, so
creating models basically requires them to go into the
database. Once you've loaded them, they persist, so you
can run the (randomised) race as many times as you want
without needing to reload.

Now run the race!

    $ buggy_race.run_race()

This loads the buggies *from the database* (not the CSV,
see above), asks you for a point-cost cutoff, and then
applies the rules to disqualify any who don't qualify:
it identifies each disqualified buggy together with the
rules (multiple) it violated (RACE_COST_THRESHOLD is
the only variable one); all these violations are potentially
motivating for students to address in their buggy editors,
so are presumably important to provide to the students.

Then it runs the race: you can see it's *partially*
implemented. Didn't get finished :-( A bit of thought is
required to make this log parseable so it could be consumed
and then replayed by JavaScript on the browser (this is
why the buggy penant colours/patterns were collected and
are exposed here: presumably those would be used as the icons
on the playback screen.)

Output is written to `race.log`

You can leave the arena with

    $ quit()


