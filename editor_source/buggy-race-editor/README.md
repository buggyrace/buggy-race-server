Racing Buggy Editor
===================

> This is the "buggy editor" component of the Buggy Racing project


Overview
--------

This is the skeleton of an application for editing a racing buggy.

It runs as a webserver so you can edit the configuration of a buggy in your
browser. The editor can then generate the data, in JSON format, that you need
in order to enter races on the race server.

The application is written in Python3 using the
[Flask](https://palletsprojects.com/p/flask/) micro-framework.

> It's also written in a way which you can and should fix! You should be able
> to get it up and running (with SQLite) without needing to change the code...
> but from that point on you'll need to change pretty much everything to make
> it better. 

* see the race server for technical & project information


Installation & set-up
---------------------

Getting the editor running on your own machine differs depending on which
operating system you're using. The principles are the same, but the way to
execute them is slightly different.

Start by logging into the race server.
Depending on how the project has been run, following the instructions there
may automatically _fork_ the repo into your own GitHub account for you. Then
clone that fork from your GitHub account onto your own machine.

> If you don't have access to your own machine, it's possible to use
> [repli.it](https://replit.com) or [pythonanywhere](https://www.pythonanywhere.com) instead.


### Prerequisites

You must have Python3 installed:

* [Python 3](https://www.python.org) for programming

It's best if you have Git installed too:

* [Git](https://git-scm.com) for version control

> If you don't/can't install git, you _can_ download the source code manually
> but we recommend you don't do it that way.

If Python or git are not already installed on your machine, see the
downloads/installation instructions on their respective websites.


### Installation

Before you can run the buggy editor webserver you need to install some
Python modules.

> **About virtual environments**
>
> Any software project depends on specific versions of tools (for example,
> Python 3.8) and their associated libraries. You need these to be installed
> before you can use them.  Instead of installing them on your whole machine
> (which might be a problem if other projects need different versions of the
> same libraries) it's best to create a virtual environment just for this
> project, and work inside that.
>
> However, if you're totally new to programming, the extra complication of
> using a virtual environment probably isn't worth it (yet). But if you want
> to find out more, see the the tech notes!

Use the `cd` command to change to the directory that you got from either
cloning or unzipping the source code (it will probably be called something
like `buggy-race-editor`).

Use pip — which should have been installed as a side-effect of installing
Python — to load the required modules (including Flask, the webserver
framework). The file `requirements.txt` tells pip what modules are needed.

    pip install -r requirements.txt

Finally, set up the database:

    python3 init_db.py

This creates an SQLite database in a file called `database.db`.

There's no configuration file to edit (yet). You're ready to go!

> If `pip` or `python3` don't work for you: ask for help! The details differ
> depending on what operating system you're using and how you installed
> Python.


Running the server
------------------

Once the source code is on your machine, the dependencies are installed, and
the database initialised, you can run the Buggy Editor.

If you're not already in the project's directory, `cd` into it.

> If you're using a virtual environment, remember to activate it now.

Run the application with:

    python3 app.py

The webserver is running on port 5000 (that's the default for Flask apps). If
you make a request for a web page, it will reply with one!

Go to [http://localhost:5000](http://localhost:5000) in your web browser.
You haven't specified which file you want, so you'll get the `/` route, which
(you can see this by looking in `app.py`) invokes the `index.html` template.

You can see the webserver's activity in the terminal, and the result of its
action in the browser.


### Shutting down the server

When you want to stop the program running, in the terminal where the webserver
is running, press Control-C. This interrupts the server and halts the execution
of the program. (If you go to [http://localhost:5000](http://localhost:5000) in
your web browser now, you'll see a message saying you can't connect to the
server — because you've killed it: it's no longer there).

> If you were running in a virtual environment, you can deactivate it by
> issuing the command `deactivate`.

You're done!


### Extra detail: setting `FLASK_ENV`

It's best if you run in Flask's _development environment_. To do that, set the 
environment variable `FLASK_ENV` before you run `appy.py` to `development`.
Once you've done this, it's good for the rest of the session.

On Windows cmd/Powershell do:

    $env:FLASK_ENV = 'development'

On Linux or Mac:

    export FLASK_ENV=development


---

From the [Buggy Racing project](https://www.buggyrace.net)
