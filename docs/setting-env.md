---
title: setting env
---

{% include common.html %}

# Setting Flask environment variables


---

You can pass some settings into your buggy editor (which is a Flask app) using
[environment variables](https://en.wikipedia.org/wiki/Environment_variable).
The most immediately useful one of these is

`FLASK_ENV`

which _ideally_ should have the value `development` while you are working
on your project.

Environment variables are a feature of the operating system, not Python,
so how you set them differs depending on what platform you are on.

You can check if your setting of `FLASK_ENV` has worked by looking at the
output of your webserver when you run it (with your Python command). You should
see:

    * Environment: development


## On Windows

### Use the Registry

You can set environment variables in the registry.
Find the  _System Properties_ dialog  in the Windows Control Panel.
There's an _Environment Variables_ button there. Good luck. 

### With Powershell

If you do this:

    set FLASK_ENV=development

That should set `FLASK_ENV` for the remainder of the session. When you run
`py app.py` or `python3 app.py` (depending on what python command you're
using it) should pick it up.

### With Git bash

Git bash on Windows mimics the way things work in Unix, so follow the Unix
instructions below.


## On Unix/Mac

Use `export` to set the variable:

    export FLASK_ENV=development

That should set `FLASK_ENV` for the remainder of the session. When you run
`python3 app.py` it should pick it up.

Alternatively, you can set the variable _as you launch the command_. This method
is popular because it's explicit:

    FLASK_ENV=development python3 app.py

## Any platform:

### Tell Python to load it from .env

This is a nice solution because it works on all the platforms and if you do it
once, it sticks until you delete the `.env` file.

If you are using a virtual environment, make sure you've activated it _before_
you attempt to install the `dotenv` module (because you want pip to install the
new module in that environment).

Install the `dotenv` module by doing:

    pip install python-dotenv

If you can't get `pip` to work (maybe "no such command") you can try this
instead (again use `python3` or `py` depending on what you Python command is):

    python3 -m pip install python-dotenv

Once `dotenv` is installed, when Flask runs it will notice if there's a file
called `.env` where you are, and if there is, will load any environment
variables declared inside it.

So make a file called `.env`. This can be tricky on Windows because most
editors try to add `.txt` to the end. If you use Windows explorer and you do
_not_ have "show extensions" enabled (so you see `app` instead of `app.txt`)
change that because in CompSci you need to know the real names of the files
you're working with.

Edit `.env` so it contains this line:

    FLASK_ENV=development

And you're done. Now when you run your app, it should automatically pick
up any environment variable settings that are in that file.


{% include footer.html %}
