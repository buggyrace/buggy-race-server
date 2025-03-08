#  0-GET

## Get the source code

### Problem

The source code for the app you're going to be developing already exits: you
need to get your own copy of it to a place where you can edit it and run it.

### Solution

* If you don't have a account on [GitHub](https://github.com) already,
  create one and log in.

* Go to the [GitHub repo of the buggy editor](%BUGGY_EDITOR_REPO_URL%).
  You can't make changes to this repo, but you can make your own copy of
  it on GitHub by _forking_ it into your own account.

* Click on the **Fork** button (near the top right — you'll only see it if
  you are logged into GitHub). This will clone a copy of the repo into your own
  GitHub account. 
  
* Go back to your own GitHub account in the browser, and you'll see the forked
  copy of the repo is now there: navigate to it by clicking on the title.

* Click on the green **Code** button to get the code:

* **If you are using Git**: you need to do `git clone` to get a copy of those
  files onto your own machine, and to do that you'll need to copy one of the
  URLs (either starting with `https:` or `git:`). The difference between the
  two is just (at this stage) about how Git connects to the repo, and might
  not make any difference if the repo is public. Click on either HTTPS or SSH
  and copy the command shown in that tab. You'll need to use this URL as
  the argument to the `git clone` command on the command line of your own
  machine.

* **If you are not using Git**: you can download the ZIP file instead. If you
  do that you won't have any version control information when you unizp the
  files.

### Hints

* If you clone the repo from GitHub, remember that you will only be able to push
  any changes back up if you have write permission on that repo. That's why
  you forked the original repo into your own GitHub account first. If you clone
  directly from the original repo, you won't be able to push any changes back
  up.

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
