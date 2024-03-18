#  0-GET

## Get the source code

### Problem

The source code for the app you're going to be developing already exits: you
need to get your own copy of it to a place where you can edit it and run it.

### Solution

* We've set the [buggy race server](%BUGGY_RACE_SERVER_URL%) up so that if you
  log into that, the source code for your buggy editor will be forked into
  your GitHub account for you.

* You'll need an account on [GitHub](https://github.com) — if you haven't got
  one already, sign up. The process for getting your copy of the source code
  is a little simpler if you are already logged into GitHub when you start,
  so... log into your GitHub account.

* Log into the [buggy race server](%BUGGY_RACE_SERVER_URL%). If you haven't
  connected your race server account to your GitHub account yet, you'll see
  a button inviting you to do so — click the **Connect your GitHub account**
  button.

* You'll be asked to confirm that the race server (actually it's OAuth app)
  can have access to your repo on GitHub — confirm that (you'll get an email
  from GitHub letting you know this just happened)

* When your GitHub account has connected to your race server account, you'll
  see a button marked **Fork Buggy Editor repo**. Click that button to _fork_
  our buggy editor repo (the source code you're going to work with) into your
  GitHub account. It will take a few seconds, so be patient after clicking
  the button.

* We'll also inject these tasks directly into your GitHub repo as
  [GitHub issues](https://docs.github.com/en/issues) so you can use them if
  you want to.

* **If you are using Git**: you need to do `git clone` to get a copy of those
  files onto your own machine, and to do that you'll need to copy one of the
  URLs (either starting with `https:` or `git:`) — you choose between them by
  clicking on HTTPS or SSH tab. The difference between the two is just (at this
  stage) about how Git connects to the repo, and might not make any difference
  if the repo is public. 

* **If you are not using Git**: you can download the ZIP file instead. If you do
  that you won't have any version control information when you unizp the files.

### Hints

* If you clone the repo, because you're cloning from _your_ fork up on GitHub
  (and not ours), you'll be able to push any changes you make back up, because
  your `origin` repo is in your account (in which you have write access), not
  ours (in which you do not).

* If you download a zip, make sure you unzip the files into a directory
  that is in a suitable place and you'll be able to find.

* It's important that you _extract_ the files from the zip — do **not**
  start working, or editing, the files while they are still inside the
  archive. Be careful!

* If you're not comfortable finding your way around the file system yet,
  see the [CompSci superbasics](%SUPERBASICS_URL%/file-system).


# 0-RUN

## Get app running and view it in a browser 

### Problem

You need to be able to deploy the webserver, contained in `app.py`, so you can
view it in your web browser.

### Solution

Run the python code so it listens on a port somewhere you can point your
browser at.

### Hints

* You should also install the Python libraries it needs (including Flask).
  You probably should create a virtual environment to do this, and then use
  `pip` to install the requirements. See the instructions in the README.

* If you're working on any other Python projects as well as this one, it
  might be helpful to use a _virtual environment_. For more information
  see the [Python docs on venv](https://docs.python.org/3/library/venv.html).

* Although websites — of course — run on remote webservers, while you are
  developing the code (that is, working on this project) you run your own
  instance of it on your own machine.

* The special IP address `127.0.0.1`, which has the name "localhost", maps to
  the local machine, so if you run your app locally you can find it there.
  Servers also need to specify what port they are listening on (by default,
  Flask will use 5000) — so when you runn `app.py` you should be able to see
  your buggy editor in your browser at
  [http://localhost:5000](http://localhost:5000)

* See the[tech note about localhost](%BUGGY_RACE_SERVER_URL%/tech_notes/localhost).


