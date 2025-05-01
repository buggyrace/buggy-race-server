Racing Buggy Editor
===================

> This is the "buggy editor" component of the Buggy Racing project


Overview
--------

This is the skeleton of an application for editing a racing buggy.

It runs as a webserver so you can edit the configuration of a racing buggy in
your browser. The editor can then generate the data, in JSON format, that you
need in order to enter races on the race server.

The application is written in Python3 using the
[Flask](https://palletsprojects.com/p/flask/) micro-framework.

> It's also written in a way which you can and should fix! You should be able
> to get it up and running (with SQLite) without needing to change the code...
> but from that point on you'll need to change pretty much everything to make
> it better. 

* See the race server for technical & project information


Installation & set-up
---------------------

> If you don't have access to your own machine, it's possible to use online
> platforms like [repli.it](https://replit.com) or
> [pythonanywhere](https://www.pythonanywhere.com) instead.

You must have [Python]((https://www.python.org)) installed (at least version 3.9).

If you're not already in the project's directory, `cd` into it.

Install the Python modules: 

    pip install -r requirements.txt

Set up the database by running the `init_db.py` script (this creates an SQLite
database in a file called `database.db`):

    python3 init_db.py

That's it. You're ready to go!


Running the server
------------------

Run the buggy editor application with:

    python3 app.py

The webserver is running on port 5000. If you make a request for a web page, it
will respond with one!

Go to [http://localhost:5000](http://localhost:5000) in your web browser.
You haven't specified a path, so you'll get the `/` route, which uses the
uses the `index.html` template (you can see this by looking in `app.py`).

You can see the webserver's activity in the terminal, and the result of its
action in the browser.


### Shutting down the server

When you want to stop the program, in the terminal where the webserver is
running, press Control-C. This interrupts the server and halts the execution of
the program. (If you go to [http://localhost:5000](http://localhost:5000) in
your web browser now, you'll see a message saying you can't connect to the
server — because you've killed it: it's no longer there).


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
