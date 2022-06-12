# CS1999-buggy-race-server Development

## Jasper's Notes:

### Getting started

1. `pip install -r requirements.txt`
    * Requires gevent which sometimes needs special treatment on macos. Specifically, if homebrew is used to install stuff then it may have installed some header files (`/usr/local/header/uuid/uuid.h`) from `util-linux`. I had to remove them to get gevent to compile.
2. `flask db init`
3. `flask db upgrade`
4. `flask db migrate`
5. `cp env.example .env`
  * add your name or a preferred username to `ADMIN_USERNAME`
  * set or use the default value for `REGISTRATION_AUTH_CODE`, you will need it for registering accounts.
6. `npm install`
7. Run the flask app
  6.1. `npm start`
    * Skips everything and does the front end build magic and starts the flask app.
  6.2. `flask run`
    * The flask app and other settings are defined in `.env`
  6.3. `npm run webpack-watch` 


## Dave's Notes

OAuth Application registered on GitHub by owner davewhiteland
(currently organisation's can't register apps)

* https://github.com/settings/applications/1613423


### How to run a race 

Here's how I ran the race, having cloned the repo:

    $ cd CS1999-buggy-race-server

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
rules (multiple) it violated (RACE_COST_THRESHHOLD is
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


