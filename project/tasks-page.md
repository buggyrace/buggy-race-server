#  0-GET

## Get the source code

### Problem

The source code for the app you're going to be developing already exits: you
need to get your own copy of it to a place where you can edit it and run it.

### Solution

* Go to the home page of the [buggy race server](%BUGGY_RACE_SERVER_URL%)
  and click on **Get the code**.

* That will either take you to a page with more instructions, or download
  a zipfile containing the files.

* Unzip it (extract the files inside it) in a directory on your computer.

### Hints

* Make sure you unzip the files into a directory that is in a suitable
  place and you'll be able to find.

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
