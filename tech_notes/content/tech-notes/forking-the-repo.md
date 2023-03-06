Title: forking the repo


# Forking the repo

* Task [0-GET Get the source code]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-0-get)

---

The repo (or repository) is the collection of all the files you need for the
buggy editor you're developing. It is _like_ a directory, but with a very
significant difference: the repo contains not the just files, but also the
history of those files, and other metadata that the version control software
Git can read.

The project requires you to take start with the code we've got, and develop
it according to the tasks we've set out for you, into your own buggy editor.

You make a copy of of our code, and edit that. _Forking_ (and then _cloning_)
is the way you're going to make that copy.

## What does _forking the repo_ mean?

Forking happens up on GitHub. It means you make your own, personal copy of our
repo. [Our repo]({{ BUGGY_EDITOR_GITHUB_URL }}) is in our GitHub account (the repo is
public, so you can see it but you can't change it — that is, it's read-only).
After forking, your repo is in _your_ GitHub account.

Significantly, your repo _knows_ it has been forked from ours. We're not going
to exploit that in the Buggy Editor project, but it's worth knowing that if you
make changes to your code that you think we might like to pull back into ours,
you'd create a Pull Request (see below). GitHub is set up to make it simple to
make pull requests back to the original repo — this is one of the common
mechanisms of open source software.

> _Forking_ really means making another copy of the repo. Really it's the
> same operation as _cloning_ but the intention is very clear: you're making
> a parallel version of the code, so you can work on that code independently
> of the original. Your clone's relationship with the original does exist
> in a way that is different from simply copying (in git parlance it's
> your fork's _upstream repo_ — but be a little careful because "upstream"
> turns up in a slightly different context in git elsewhere too).
>
> Forking doesn't only happen on Github — you can fork in any version control
> system, because it's really about _how_ you are making a parallel, 
> contemporary copy — but GitHub has made it very common by making it
> simple to do through the GitHub web interface.

## How to fork your repo

For this project, we don't want you to do this by hand (although doing so is
straightforward: if you're logged into GitHub, you can just click on the
**fork** button on the repo you want to copy).

Instead, log into the [race server]({{ BUGGY_RACE_SERVER_URL }}).
You'll be invited to log in to your GitHub account — do that (you can create
one then, when you do it). Once you've done that, the server will fork the
repo into your account for you. It _also_ injects the tasks you're going to
do as _GitHub issues_.


## Cloning your fork

Once you've got a copy of our repo in your GitHub account, you can clone it
onto your own (local) machine. To do that you'll need git installed on your
machine. (Check first: you _might_ have it already).

* [downloads for installing git](https://git-scm.com/downloads)

When you're got git installed, there are a number of ways to use it (including
a GUI), but ideally you need to get to a command line:

* on Windows, run `git bash` (which was installed when you installed Git)

* on Unix or the Mac, open a terminal window

Go the the directory in which you want to do your work, and then clone the
repo — that means git will copy the whole repo from GitHub down onto your own
local disk. It's not "just" copying a directory, because it's bringing all the
meta data about the organisation and, crucially, history of those files too.

To do this, go to **your forked repo** (make sure it's your fork, that is, it
is the one _in your GitHub account_ — not (our) original one that you forked it
from) and press the green **Code** button. Copy the URL and paste it onto the
command line after `git clone` like this:

    git clone git@github.com:your_github_username/{{ BUGGY_EDITOR_REPO_NAME}}.git

When you press ENTER, you'll see the files being copied down (it won't take
long). A directory named `{{ BUGGY_EDITOR_REPO_NAME}}` will appear. That's your
local repo.

There's a little more setup to do before you can push any changes you make
back up to your forked repo, but that's the clone done.

---

## About forking and Pull Requests

Remember, you don't need to do this manually for this project, but see the
[explanation of forking on GitHub](https://guides.github.com/activities/forking/).
You can fork any repo you have read access to up on GitHub.

One application of forks is that you can make your own changes to your fork (it's
your copy now, remember), test them, and then offer those changes back. You can
request that the owner of the original repo _pulls in your changes_. This
is called making a "pull request". This mechanism allows the owner of the
original repo to maintain control over their code (it can be read-only) whist
allowing other people to develop on it non-destructively.

Pull requests are also used between developers on the same team — working on
the same repo, where they _do_ all nominally have write access — as a mechanism
to invite (or enforce) code review and approval before changes to code are
accepted. When pull requests are accepted, the code changes are merged into the
project.


