# Installation notes

This app started out as a
[cookiecutter-flask](https://github.com/cookiecutter-flask/cookiecutter-flask).
which means its structure was inherited from that, including these
installation/running notes.

There's a quite a lot that came with cookiecutter-flask that turned out to be
more of an overhead than a boon, but it is is what it is now. Basically:
first-time setup requires some patience, but once you're through that you
should be OK.

Cookiecutter-flask ships with docker support too but that is untested here —
if you're the kind of person who likes docker, then that's probably still all
intact: see original documentation further down.

---

## Local "manual" installation:

If you're going to do any development on the server, install it locally and
then you can fiddle about to your heart's content.

It's a good idea to have a local `venv`. If you don't know about `venv` you
can skip this first step... but it's probably best to investigate
[Python's virtual environments](https://docs.python.org/3/library/venv.html)
first.

```bash
cd <this project dir>
python3 -m venv venv
source venv/bin/activate
```

That's it: now any python modules you install are local to this project; you
won't be messing with other Python projects on your machine, and they won't be
tampering with this one.

Install the Python modules the project requires, using pip. The file `dev.txt`
lists those requirements in a format pip can read:

```bash
pip install -r requirements/dev.txt
```

You *must* set some configuration settings before you can run, and these are
not already in the repo (because if they were, your changes would be
overwritten if you pull down a more recent version in the future). So copy the
example file and call it `.env`...

```bash
cp env.example .env
```

...and edit that `.env` file. (Note that on Unix systems that's a hidden file
because it starts with a dot). You must not change the name of the file: if it's
not called `.env` Flask isn't going to use it. It's possible you won't need to
make any changes there — except maybe the name of the admin user (you haven't
made any users yet).

Next, set up the database. By default the local install uses an SQLite database
called `/tmp/dev.db` which is fine for development. The following creates it
and builds the tables inside it:

```bash
flask db init
flask db migrate
flask db upgrade
```

Once you've done that, you don't need to do it again — unless you make any 
changes to the database structure, in which case please add migrations using
alembic.

The project uses webpack to gather all the static assets (Javascript, CSS, etc).
The webpack utility is uses node.js, which is managed by `npm`, so you'll need
to install that first:

```bash
npm install
```

Once it's created the (massive, sigh) `node_modules` directory, you should be
good to go:

```bash
npm start
```

Running that _might_ tell you that you need to update `yarn` (sigh) so you can
do that too. (It might need a `npm build run` too).

When that's all done... you're ready to run the server:

```bash
flask run
```

That will run the buggy-racing server website locally on port 5000: hit it
in a browser on [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

Note you won't be able to log in until you've made an admin user: go to
register and supply the authorisation code (it's one of the config settings
you edited in the `.env` file at the start). Make sure the username you
register is listed as an admin. For example, with these settings...

```yaml
AUTHORISATION_CODE=please
ADMIN_USERNAMES=jane
```

...you'd need to supply `please` as the auth code, and `jane` as the username
to create an admin user called `jane`. If you change the auth code to be empty
then registration is disabled. You won't care about that on this, your local,
installation — but it's how registration is constrained on the production site.
Normally registration only happens once, at the start of term, and then can be
so disabled.

---

## Viewing the static (GitHub pages) site

The `docs/` directory is the root of the GitHub pages site that contains crucial
information for the students.

You can run that locally too so you can edit and test it before publishing it
(by pushing it, in the default branch, up to GitHub — assuming you've enabled
the repo to publish GitHub pages from `docs/`).

The publication of those pages requires Jekyll (that's the tool GitHub pages
uses). To set that up, you'll need Ruby installed and bundler. Ideally, use
`rbenv` or `rvm` to manage a local environment for your Ruby gems.

The Jekyll site is effectively contained within the `docs/` directory:

```bash
cd docs/
bundle install
```

The reads the dependencies from the `Gemfile` and installs what it needs.
Then you can generate the site with

```bash
bundle exec jekyll serve
```

...and hit [http://127.0.0.1:4000](http://127.0.0.1:4000) for the static site
that is automatically published whenever you push changes to `docs/` up to
GitHub.

Note that `utils/generate_tasks.py` changes the contents of the rather important
task list in this static site, so you might need to look into that too.





---


## Docker Quickstart

This app can be run completely using `Docker` and `docker-compose`. These notes
come from the cookiecutter-flask project and have not been tested.

There are three main services:

To run the development version of the app

```bash
docker-compose up flask-dev
```

To run the production version of the app

```bash
docker-compose up flask-prod
```

The list of `environment:` variables in the `docker-compose.yml` file takes
precedence over any variables specified in `.env`.

To run any commands using the `Flask CLI`

```bash
docker-compose run --rm manage <<COMMAND>>
```

Therefore, to initialise a database you would run

```bash
docker-compose run --rm manage db init
docker-compose run --rm manage db migrate
docker-compose run --rm manage db upgrade
```

A docker volume `node-modules` is created to store NPM packages and is reused
across the dev and prod versions of the application. For the purposes of DB testing with `sqlite`, the file `dev.db` is mounted to all containers. This volume mount should be removed from `docker-compose.yml` if a production DB server is used.


## Deployment

When using Docker, reasonable production defaults are set in `docker-compose.yml`

```text
FLASK_ENV=production
FLASK_DEBUG=0
```

Therefore, starting the app in "production" mode is as simple as

```bash
docker-compose up flask-prod
```

If running without Docker

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL="<YOUR DATABASE URL>"
npm run build   # build assets with webpack
flask run       # start the flask server
```

## Migrations

If you change a model such that the database table storing it needs to change
too, run a migration:

```bash
flask db migrate
```

This will generate a new migration script. Then run

```bash
flask db upgrade
```
make sure you commit the file(s) that creates to version control, because if
you've deployed to heroku, it automatically notices new migrations and updates
the database up there when you push them.

## Asset Management

Files placed inside the `assets` directory and its subdirectories
(excluding `js` and `css`) will be copied by webpack's
`file-loader` into the `static/build` directory. In production, the plugin
`Flask-Static-Digest` zips the webpack content and tags them with a MD5 hash.
As a result, you must use the `static_url_for` function when including static content,
as it resolves the correct file name, including the MD5 hash.
For example

```html
<link rel="shortcut icon" href="{{static_url_for('static', filename='build/img/favicon.ico') }}">
```

If all of your static files are managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in ``.env``:

```text
SEND_FILE_MAX_AGE_DEFAULT=31556926  # one year
```

## Heroku

Before deploying to Heroku you should be familiar with the basic concepts of
[Git](https://git-scm.com/) and [Heroku](https://heroku.com/).

Remember to add migrations to your repository. Please check `Migrations`_ section.

**Note:** `psycopg2-binary` package is a practical choice for development and
testing but in production it is advised to use the package built from sources.
Read more in the [psycopg2 documentation](http://initd.org/psycopg/docs/install.html?highlight=production%20advised%20use%20package%20built%20from%20sources#binary-install-from-pypi).


Deployment by using [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli):

* Create Heroku App. You can leave your app name, change it, or leave it blank
(random name will be generated)

    ```bash
    heroku create buggy_race_server
    ```

* Add buildpacks

    ```bash
    heroku buildpacks:add --index=1 heroku/nodejs
    heroku buildpacks:add --index=1 heroku/python
    ```

* Add database addon which creates a persistent PostgresSQL database. These
  instructions assume you're using the free
  [hobby-dev](https://elements.heroku.com/addons/heroku-postgresql#hobby-dev)
  plan. This command also sets a `DATABASE_URL` environmental variable that
  your app will use to communicate with the DB.

    ```bash
    heroku addons:create heroku-postgresql:hobby-dev --version=11
    ```

* Set environmental variables (change `SECRET_KEY` value)

    ```bash
    heroku config:set SECRET_KEY=not-so-secret
    heroku config:set FLASK_APP=autoapp.py
    ```

* Please check `env.example` to see which environmental variables are used in
  the project and also need to be set. The exception is `DATABASE_URL`, which
  Heroku sets automatically.

* Deploy on Heroku by pushing to the `heroku` branch

    ```bash
    git push heroku main
    ```


