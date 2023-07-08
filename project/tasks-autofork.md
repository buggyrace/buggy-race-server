#  0-GET

## Get the source code

### Problem

The source code for the app you're going to be developing already exits: you
need to get your own copy of it to a place where you can edit it and run it.

### Solution

Get the source code, ideally by using the VSCode workspace file we have
prepared for you. It will clone your Github repository onto your personal
directory in the CS Department's *teaching server*.

A requirement for the below steps is to install the main IDE (**I**ntegrated
**D**evelopment **E**nvironment) we will use for this module:
[VSCode](https://code.visualstudio.com/). This is a modern, powerful and
thorough IDE that will be a valuable asset in your toolbox! This is what needs
to happen:

* Go to the [buggy race server](%BUGGY_RACE_SERVER_URL%) and login.
* Link your account to your Github personal account.
* `Fork` the template for the buggy race editor from
  [our Github repository](%BUGGY_EDITOR_GITHUB_URL%) to yours.
* Download your *VSCode workspace configuration file* by clicking in the
  corresponding button. Store it somewhere safe.
* Open it with VSCode. It might complain that some plugins and packages are
  missing. **Do not despair**, VSCode will kindly offer to install everything
  that is necessary.
* You will be asked to input your college password a couple of times. Just type
  it every time it is requested. Wait for a bit.


After VSCodes finishes connecting you to our *teaching server*, it will be time
to get the code from Github, to your personal home directory in the server.
Do not worry, we have also automated this for you. To get a copy of your buggy
race editor repo to the server, do:

* go to the *terminal* tab in VSCode, located in the top panel. Then, click on
  *run task* and a list of tasks will appear. Choose the one starting with
  `git clone https://github.com/` and wait.
* The previous step *cloned* your **remote Github repository** to a **local
  version** which, in this case, lives in the teaching server!
* If you click on *Open file* and you look in your *home directory*, you should
  find a folder with a name `%BUGGY_EDITOR_REPO_NAME%`.
* Open that folder and compare its contents against those in the remote repo you
  previously forked, they are the same!
* You might get asked for your college password a couple of times in the above
  step, this is normal.
* If the `%BUGGY_EDITOR_REPO_NAME%` folder **is not** in your home directory,
  then probably something went wrong. Try to reproduce the above steps once
  more.


### Hints

* We've set the [buggy race server](%BUGGY_RACE_SERVER_URL%) up so that if you
  log into that, and then log into GitHub, the editor source code will be
  forked into your GitHub account for you.

* This is the easiest way to get started!

* (We'll also inject these tasks directly into your repo's issues for you too).

* The source code for your webserver app is in
  [this Git repository](%BUGGY_EDITOR_GITHUB_URL%) (but don't use that repo!
  Fork youn own copy of it — see above!).

* The VSCode workspace file you have downloaded from the Buggy Race Server is
  configured to run the command `git clone` on your forked Buggy Race Editor. 

* You could download it as a zip, but we recommend you `git clone` your forked
  repo instead... because that way you can push your changes back up to your
  GitHub account.

* Forking in this context means making your own copy of it up on the GitHub
  servers (that then becomes the GitHub repo you are pushing back up to). The
  point of forking first is that _our_ repo is read-only (you can't change it)
  but when you fork it you make your own copy on GitHub... and because it's
  your copy, you can make changes.

* To fork manually: first, log into GitHub, then go to
  [our copy of the repo](%BUGGY_EDITOR_GITHUB_URL%) and click on Fork (on the
  top right of the screen). (But: don't do this! See the first hint ↑ up there).

* We expect you to do your development on our _teaching server_ (where you can
  run Python3 and where everyone will get an uniform coding experience): you
  can't run your Python code on Github so that's why we need to do a _clone_
  operation to get the code onto the server.

* Notice that it does not matter from what machine you are working, you will
  always be connected to our teaching server and you will do all the
  development required for this module there. We have configured VSCode so that
  when you run the provided *workspace file*, it will use your college
  credentials to perform a `ssh connection` to your home directory in the
  server. This is great because it is tightly aligned to the spirit of this
  project: interactions with servers. If for some *catastrophic* reason you do
  not use our pre-configured VSCode workspace file, you _can_ open it in
  repl.it instead *but we don't recommend that* as a first choice.
  
* The machine you are having in front of you *e.g.* your laptop or workstation,
  the machine you are connecting to *i.e.* the teaching server, and the tools
  you're using, are called your _development environment_. Setting that up is
  an important part of the start of the project. If you are stuck, ask for help!

