Title: using virtual environments


# Using virtual environments

* Task [0-RUN Get app running and view it in a browser]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-0-run)

---

## Background: different versions of Python and Python modules

When you run a Python program like your buggy editor application, you are
_really_ running the _Python interpreter_. It's that application (the
interpreter) that is running: it follows the script that's in your buggy
editor's `app.py` file.

The Python interpreter includes the
[standard library](https://docs.python.org/3/library/index.html) — lots of
useful modules that your `import` statements are using. Then there are
additional modules that your app might be relying on that you will need to
install (with a tool like `pip`) and `import`. The most obvious one of those in
your buggy racing editor app is Flask, but Flask itself depends on other
modules too.

All these things — the Python interpreter, and its library modules, including
the extra ones you've installed (with `pip`) — are loosely called your "Python
environment".

With that in mind, it follows that you _could_ have different copies of the
Python interpreter. When you're first introduced to Python, you don't worry
about this because Python is Python, right? But there can be small (and some
not-so-small) differences between Python versions, and module versions, so
sometimes you might want to choose which one you run.

However, as your programs get increasingly complicated, and you start to have
more than one project on the go, you run into the risk that some of these
versions will contradict others. One script might have specific requirements
that require versions of a module or even the interpreter that differ from
another script. At this point you'd need to be able to switch between Pythons
or Python libraries depending on which script you were working on.

That's why **virtual environments** exist. They are way of making a local copy
of the Python interpreter, and letting it manage its own copy of the modules,
keeping it all local to the project.

> In fact, Python's (lightweight) virtual environment does not make a duplicate
> of the interpreter itself if your system already has one — it uses
> [symbolic links]({{ SUPERBASICS_URL }}/files/symlinks/)
> instead... but the effect is the same.

## Do you need to use a virtual environment?

Technically, you do not _need_ to use a virtual environment. If the buggy
racing project is the only Python project you are working on, maybe you are OK
using your "System" Python. This means that any Python modules you install
(such as Flask) will be installed in the "System" Python library. This is OK
(provided you have admin privileges on the machine to do it)... until you bump
into the problem described above. When you have scripts requiring different
Python or module versions at the same time, this doesn't work.

So, if you're going to be studying or working with Python, you _must_ understand
how to use Python's virtual environments. Get into the habit of setting up a
virtual environment whenever you start a new Python project of any complexity!

## The `venv` module

Official docs:

* [`venv` module](https://docs.python.org/3/library/venv.html)
* [Create and Use Virtual Environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments)

Using a virtual environment is so useful — and so common — that Python ships
with a module for setting up a *v*irtual *env*ironment, called `venv`. It
creates a directory (which by convention, you typically call `venv` too), into
which it puts a copy (or symlink) to the Python interpreter, as well as any
Python modules or packages you install.

On the command line, the basic way to create the virtual environment is with
this command (some systems might use the `python` command instead):

    python3 -m venv venv

The `-m env` is running the module, and the second `venv` is the name of the
directory to create (so make sure you issue this command in the right place —
that's typically the root directory of your project).

_Important:_ This has created the virtual environment but it hasn't _activated_
it. The way to do that varies slightly depending on what platform you're using.
You need to _activate_ it in each session (in practice, that means in each
terminal you open). If you don't activate the virtual environment, you'll be
using your system Python, not the local one. Often this will work... to start
with.


### What to call your virtual environment

The second argument you provided was the name of directory in which the virtual
environment will be managed and stored. By convention, it's called `venv` or
`.venv` (the dot prefix indicates it's a
[hidden folder]({{ SUPERBASICS_URL }}/files/hidden-files/)).

There are circumstances when you might want more than one virtual environment
(especially for testing). In that case you'd need different names for each
virtual environment. But if you're new to virtual environments, it's probably
best to stick with `venv`.

If you're using Git, you'll always want your `venv` directory to be excluded
from version control, so its name should appear in the repo's `.gitignore` file.
Your buggy editor repo's `.gitignore`  already has `venv` and `.venv` (and some
others) in anticipation of you using one of the conventional names.

### How to activate a virtual environment

The directory you just created (and probably called `venv`) contains a script to
run which activates it. In fact it contains more than one: _which_ script you
use, and how to run it, depends what operating system you're on:

* Linux/MacOS: `source venv/bin/activate`
* Windows: `venv\Scripts\activate`

### How to deactivate a virtual environment

Often, you'll deactivate a virtual environment by ending the session it's
running in (by closing the terminal window, for example). But you can also use
the `deactivate` command (which was set up for you when you activated it).

## Instructions for VSCode

Many interactive development environments (IDEs), like VSCode, encourage the
use of virtual environments, and will use one if you've created it, or offer
to create one when you first fire up a new Python project.

If you're using Visual Studio Code, there is more than one way of setting up a
virtual environment. Here's one way to do it. The commands are slightly
different on depending on the platform you're on, so we've separated them here.

Once you've set up a virtual environment, if you ever run a Python script by
clicking on the **Play ▷** button, you'll need _that_ to be using the same
environment too. VSCode will notice the first time you do this if there's a
new environment, and offer to use it: you should accept this recommendation.

### Unix or Mac users:

* Open a new Terminal in VSCode using the menu **Terminal → New Terminal**. Run
  `pwd` and confirm you are in the `{{ BUGGY_EDITOR_DIR_NAME }}` folder. If not,
  change directory into it with `cd`.

* Run `python3 -m venv venv` and select "Yes" when the popup says "We noted a
  new environment has been created. Do you want to select it for the workspace
  folder?". You now have a virtual environment called `venv`.

* Run `source {{ BUGGY_EDITOR_DIR_NAME }}/bin/activate` - this will activate the
  new virtual environment.

* To confirm you are using the virtual environment, run `which python`. This
  should return a directory ending in `{{ BUGGY_EDITOR_DIR_NAME }}/venv/bin/python`.

### Instructions for Windows users:

* Open a new Powershell Terminal in VSCode using the menu
  **Terminal → New Terminal**. Run `pwd` and confirm you are in the
  `{{ BUGGY_EDITOR_DIR_NAME }}` folder, if not, change directory into it.

* Run `python -m venv venv` and if it appears, select "Yes" when the popup
  says "We noted a new environment has been created. Do you want to select it
  for the workspace folder?". You now have a virtual environment called `venv`.

* Run `venv\Scripts\activate` - this will activate the new virtual environment.

* To confirm you are using the virtual environment, run `where python`. This
  should return a directory ending in `{{ BUGGY_EDITOR_DIR_NAME }}/venv/bin/python`.

## "Module not found"?

One consequence of getting your environments muddled is that your Python gives
errors like:

    ModuleNotFoundError: No module named 'flask'

...even though you are sure you've installed it with `pip`. If this happens,
it usually means the Python interpreter you're running isn't the one whose
enviroment you were in when you installed the module. (It's the same error
you get if you _never_ installed Flask (oops!), because the end result is the
same: Python can't find it).
