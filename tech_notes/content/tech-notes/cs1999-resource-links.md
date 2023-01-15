Title: CS1999 link dump


# CS1999  link dump: all resources

This page contains pretty much all the links to resources for CS1999 (as of
July 2021) lifted off the Moodle and put on one page for reference.
_The Moodle is definitive_ — this is just a snapshot (for when the Moodle is
inaccessible, which includes access for people not enrolled on the course).

> The [race server](https://rhul.buggyrace.net) supports guest logins ♥  
> Just ask if you want one :-)

Staff have access to the server repo: [RHUL-CS-Projects/CS1999-buggy-race-server](https://github.com/RHUL-CS-Projects/CS1999-buggy-race-server)  
_Pull Requests welcome!_

All the videos should be accessible to anyone logged into the RHUL organisation:
if you hit one that isn't, tell us which one it is and we'll fix it!

---
<nav>
  <a href="#the-seven-phases-27-tasks">The&nbsp;seven&nbsp;phases</a> |
  <a href="#step-by-step-project-process">Step-by-step&nbsp;project&nbsp;process</a> |
  <a href="#tech-notes">Tech&nbsp;notes</a> |
  <a href="#all-the-videos-quick-links">All&nbsp;the&nbsp;videos</a> |
  <a href="#same-links-with-summary-textlinks">+&nbsp;summary&nbsp;text/links</a> |
  <a href="#information-from-the-labs">The&nbsp;labs</a> | 
  <a href="#phase-0-tasks-set-up">Phase&nbsp;0</a> | 
  <a href="#phase-1-tasks-basic-changes">Phase&nbsp;1</a> | 
  <a href="#phase-2-tasks-refined-data-entry">Phase&nbsp;2</a> | 
  <a href="#phase-3-tasks-multiple-buggies">Phase&nbsp;3</a> | 
  <a href="#useful-links">Useful&nbsp;links</a>
</nav>
---

## The seven phases (27 tasks)

There are seven phases (we expect you all to get well into Phase 3 — many of you
much further!). Phase 0 is set-up, phase 1's tasks are basic changes, and then
the phases get increasingly complex, right up to phase 6 where you can do
_anything_.

* [this is the COMPLETE TASK LIST](https://info-rhul.buggyrace.net/project/tasks/)
  
  phase 0:
  [0-GET](https://info-rhul.buggyrace.net/project/tasks/#task-0-get)
  [0-RUN](https://info-rhul.buggyrace.net/project/tasks/#task-0-run)
  [0-CHANGE](https://info-rhul.buggyrace.net/project/tasks/#task-0-change)  
  phase 1:
  [1-TEMPLATE](https://info-rhul.buggyrace.net/project/tasks/#task-1-template)
  [1-ADD](https://info-rhul.buggyrace.net/project/tasks/#task-1-add)
  [1-VALID](https://info-rhul.buggyrace.net/project/tasks/#task-1-valid)
  [1-STYLE](https://info-rhul.buggyrace.net/project/tasks/#task-1-style)  
  phase 2:
  [2-EDIT](https://info-rhul.buggyrace.net/project/tasks/#task-2-edit)
  [2-FORM](https://info-rhul.buggyrace.net/project/tasks/#task-2-form)
  [2-COST](https://info-rhul.buggyrace.net/project/tasks/#task-2-cost)
  [2-RULES](https://info-rhul.buggyrace.net/project/tasks/#task-2-rules)  
  phase 3:
  [3-ENV](https://info-rhul.buggyrace.net/project/tasks/#task-3-env)
  [3-AUTOFILL](https://info-rhul.buggyrace.net/project/tasks/#task-3-autofill)
  [3-MULTI](https://info-rhul.buggyrace.net/project/tasks/#task-3-multi)
  [3-DEL](https://info-rhul.buggyrace.net/project/tasks/#task-3-del)
  [3-FLAG](https://info-rhul.buggyrace.net/project/tasks/#task-3-flag)
  [3-TESTS](https://info-rhul.buggyrace.net/project/tasks/#task-3-tests)  
  phase 4:
  [4-USERS](https://info-rhul.buggyrace.net/project/tasks/#task-4-users)
  [4-REGISTER](https://info-rhul.buggyrace.net/project/tasks/#task-4-register)
  [4-OWNER](https://info-rhul.buggyrace.net/project/tasks/#task-4-owner)
  [4-PASS](https://info-rhul.buggyrace.net/project/tasks/#task-4-pass)  
  phase 5:
  [5-VIZ](https://info-rhul.buggyrace.net/project/tasks/#task-5-viz)
  [5-RESET](https://info-rhul.buggyrace.net/project/tasks/#task-5-reset)
  [5-RACELOG](https://info-rhul.buggyrace.net/project/tasks/#task-5-racelog)
  [5-ADMIN](https://info-rhul.buggyrace.net/project/tasks/#task-5-admin)
  [5-API](https://info-rhul.buggyrace.net/project/tasks/#task-5-api)  
  phase 6:
  [6-FREE](https://info-rhul.buggyrace.net/project/tasks/#task-6-free)


Phase 0 of the project consists of tasks 
[0-GET](https://info-rhul.buggyrace.net/project/tasks/#task-0-get), 
[0-RUN](https://info-rhul.buggyrace.net/project/tasks/#task-0-run) and
[0-CHANGE](https://info-rhul.buggyrace.net/project/tasks/#task-0-change).
That is, have you installed it on your own machine, run it, and seen
the change in your web browser?

## Step-by-step project process

* [confusion-busting step-by-step breakdown](https://info-rhul.buggyrace.net/workflow)
   of what you need to do to develop your Buggy Editor. Useful links included!

## Tech notes

The [tech notes](https://info-rhul.buggyrace.net/)
contain information specific to some of the problems you're going to hit. Some
are general, and some show you how to approach particular tasks.

* Especially for phase 0: for 0-GET and 0-RUN
  * [about forking (and cloning) the repo](https://info-rhul.buggyrace.net/forking-the-repo)
  * [using localhost](https://info-rhul.buggyrace.net/localhost) (or: why isn’t 0.0.0.0 working?)
* Things that are useful from the start
  * [use print()](https://info-rhul.buggyrace.net/print-debug)
  * [“error in update operation”](https://info-rhul.buggyrace.net/error-in-update)
    or problems saving to the database
  * [how to set FLASK_ENV](https://info-rhul.buggyrace.net/setting-env)
  * [comments](https://info-rhul.buggyrace.net/comments) in Python and HTML… and more
* Especially for phase 1: for 1-TEMPLATE
  * [templates in Flask](https://info-rhul.buggyrace.net/jinja-templates) (where the HTML comes from)
  * [routes in Flask](https://info-rhul.buggyrace.net/jinja-templates) (how it picks the right template)
* Especially for phase 1: for 1-ADD
  * [identify the template to edit](https://info-rhul.buggyrace.net/identify-template)
  * [add input tag to the form](https://info-rhul.buggyrace.net/add-input-to-form)
  * [handle the POST request](https://info-rhul.buggyrace.net/handle-post)
  * [know what’s in the database](https://info-rhul.buggyrace.net/database-structure)
  * [add new data: CREATE TABLE](https://info-rhul.buggyrace.net/adding-new-data-i)
  * [add new data: ALTER TABLE](https://info-rhul.buggyrace.net/adding-new-data-ii)
* More general things for once you’ve got going
  * [static vs. dynamic](https://info-rhul.buggyrace.net/static-vs-dynamic)
  * [cache-busting the CSS](https://info-rhul.buggyrace.net/cache-busting-css)
  * [setting a secret key](https://info-rhul.buggyrace.net/secret-key) (also: how cookies work)
  * [flash messages](https://info-rhul.buggyrace.net/flash-message)
  * [adding static content](https://info-rhul.buggyrace.net/static-content) (how to add images to your Flask app)


## All the Videos: quick links

* [video: how to backup your work](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=01fa8a35-33b9-4c75-af39-ad2e007f49c0)
* [video from lab 1: intro](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=02d9b321-6501-487b-aff1-ad21011c7740)
* [video from lab 1: introducing webservers, HTTP, and Flask](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=eeddca95-4f83-406b-88f9-ad2e00140fb5)
* [video from lab 1: asking questions in CS1999](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=eeddca95-4f83-406b-88f9-ad2e00140fb5)
* [video from lab 2: review of materials and demo of uploading buggy JSON data](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7f1ae976-57ad-49a1-bbb8-ad29001e6fcb)
* [video from lab 2: 3 ways Python errors can (and will) manifest in your buggy editor](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=417450a3-bfc5-477b-adb5-ad29002cb04b)
* [video from lab 3: why postponing task 0 is bad](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7884c1c8-8cb6-4fa4-9881-ad2f00ca7f73)
* [video from lab 3: about Flask templates](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=0adc865e-bc2a-4a7a-b2ef-ad2f00cc4bba)
* [video from lab 3: minimal Git demo](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7dce29b4-11f8-4f23-a02d-ad2f00cce79c)
* [video from lab 5: races, uploading, poster, mental health](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=9c3645e7-569f-4458-92ff-ad3e0080727f)
* [video: 0-GET forking the repo](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=d81d3a9d-5ed0-4e5a-9a1b-ad33013216a3)
* [video: 0-GET using git clone (command line)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=66081520-cc38-4ef5-a40a-ad2001272186)
* [video: 0-GET with GitHub Client](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=dc1be577-db16-4f23-b975-ad200135c7a0)
* [video: 0-GET using repl.it](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7e3e97ef-13e3-467b-a69a-ad2000eff9ab)
* [video: 0-GET by downloading the zip](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=a0110277-1fac-4ab1-ac82-ad2401613ab4)
* [video: 0-GET and 0-RUN with Git Bash (plus git bash tips!)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=6f7d98ff-1c0a-41c8-b773-ad26008e0394)
* [video: 0-RUN](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b355bae4-5bed-4d31-853d-ad20011b1e47)
* [video: 0-RUN with venv](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=3ba7bb3b-0349-4297-890a-ad20011f3396)
* [video: 0-CHANGE](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b82ac5c3-991e-4905-9fcb-ad23015afc02)
* [video: database errors](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=0fc1af57-cb02-4d29-a9fa-ad2301613b9e)
* [video: 1-VALID basic data validation](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=8d65c21e-1be6-435b-9c37-ad250004ff2c)
* [video: 2-RULES: violation check](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=05f88e99-f9c6-4b51-955b-ad2e017ef392)
* [video: 2-EDIT: preloading the form](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=fc19c085-f8aa-43d8-a6cc-ad2e018b3604)
* [video: 2-FORM: adding a select tag](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=3774efc9-4dda-4bf2-a478-ad2f000745ab)
* [video: 3-MULTI part 1: update → insert](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=9911b8d3-d49d-4ba4-9d45-ad320019608f)
* [video: 3-MULTI part 2: editing the record](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=bb971694-73c9-4ca3-b9e4-ad32001cc572)
* [video: 3-MULTI part 3: make vs. edit](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=c636244d-7bd3-4b90-95c8-ad32001ccb08)
* [video: 3-MULTI part 3½: make vs. edit "extra"](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=c69e7a99-1256-4f5a-b359-ad32002abcce)
* [video: 3-MULTI part 4: hiding the id](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=62a32660-b8ad-499d-a504-ad32002ec59a)
* [video: how to zip & submit (Windows)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=d804323c-f70a-4f97-b553-ad430088efb1)
* [video: how to zip & submit (MacOS)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=4e37d9ad-dce6-469b-ba4c-ad410145dfd4)
* [video from the final lab: retrospective](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b52db22a-7c0c-4cd6-98d8-ad4500e9aa9f)

See below for all these links, but with the summary text too.


---

## Same links, with summary text/links


* [video: how to backup your work](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=01fa8a35-33b9-4c75-af39-ad2e007f49c0)

    In CS1999 you are almost certainly working on your own machine. You must
    have a backup policy in place. Joe shows you one way to backup your work.


## Information from the labs

* [video from lab 1: intro](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=02d9b321-6501-487b-aff1-ad21011c7740)

    An intro to the labs and how to do the project: how you need to do the tasks (and phases), using the race server and the tech notes as well as this Moodle, and a little about assessment and what you have to submit
  
    [Here are the "intro" slides](https://cs.rhul.ac.uk/home/teas024/cs1999/intro/)
    (HTML of course).

* [video from lab 1: introducing webservers, HTTP, and Flask](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=eeddca95-4f83-406b-88f9-ad2e00140fb5)

    A crash-course in how webservers and HTTP work, so when you look inside the
    Flask code we've given you, you can work out how it's working.

    [Here are the "webserver, HTTP and Flask" slides](https://cs.rhul.ac.uk/home/teas024/cs1999/webserver/)
    (also HTML) including this demo of a classic
    [web page request](https://cs.rhul.ac.uk/home/teas024/http/http-200.html)
    (returning HTTP [status code 200: OK](https://http.cat/200)).

* [video from lab 1: asking questions in CS1999](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=eeddca95-4f83-406b-88f9-ad2e00140fb5)

    Joe explains how you can ask us a question privately so we can publish an
    answer that benefits everyone using
    [this form in the Teams channel](https://teams.microsoft.com/l/entity/81fef3a6-72aa-4648-a763-de824aeafb7d/_djb2_msteams_prefix_681285420?context=%7B%22subEntityId%22%3Anull%2C%22channelId%22%3A%2219%3Abc29f0e1d60b4fb9a7597ba3d7b8ade2%40thread.tacv2%22%7D&groupId=1e2cd4e1-a1df-4270-895c-fd7ca34025b3&tenantId=2efd699a-1922-4e69-b601-108008d28a2e).


* [video from lab 2: review of materials and demo of uploading buggy JSON data](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7f1ae976-57ad-49a1-bbb8-ad29001e6fcb)

    Dave visits [the Moodle page](https://moodle.royalholloway.ac.uk/course/view.php?id=8381)
    and shows you where to find things. Also, a demonstration of uploading JSON
    buggy data to the race server.

* [video from lab 2: 3 ways Python errors can (and will) manifest in your buggy editor](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=417450a3-bfc5-477b-adb5-ad29002cb04b)

    If you have an error in your Python, what does it look like? Well, it depends:

    * catastrophic errors (e,g, syntax): the webserver won't run = can't connect
    * run-time errors that are only triggered when you hit them:
      * debug mode on: status code `200`, diagnostic info in the browser
      * debug mode off: status code `500`, diagnostic info only in the server output
      * error inside a `try` block: status code `200`, page says _“error in update operation”_ (unless you change the string), **no** diagnostic information
  

* [video from lab 3: why postponing task 0 is bad](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7884c1c8-8cb6-4fa4-9881-ad2f00ca7f73)

    If you decided not to bother starting CS1999 until the CS1998 assignments
    were out of the way, something is wrong — in term 1 next year, you'll be
    running four modules, three of which have _weekly_ deliverables. Watch as
    Dave tries yet another way to convince you to take responsibility for how you
    study. Features Rocky training montage in ~~New York~~ ~~Egham~~ Philadelphia.

* [video from lab 3: about Flask templates](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=0adc865e-bc2a-4a7a-b2ef-ad2f00cc4bba)

    A quick recap/demo of what Flask templates are doing and why you have that
    `thing=thing` thing going on in `render_template()`

* [video from lab 3: minimal Git demo](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7dce29b4-11f8-4f23-a02d-ad2f00cce79c)

    You do **not** have to use Git in CS1999 — but if you want to have a go,
    here's the process:

    1. edit your code/add files/do magic
    2. `git add` those changes: you're "staging them" ready to commit
    3. `git commit` the staged changes as a single event: you must add a message
    4. `git push` the commit up to GitHub
  
    Rinse and repeat. This is a _big simplification_ of how Git should really be
    used... but that's the point — play with it now just to see your changes
    pinging up on GitHub, and thereby familiarise yourself with the process
    (you'll go into _why_ and _how_ in future years). See 
    [Atlassian for excellent, serious docs/explainers](https://www.atlassian.com/git).

* [video from lab 5: races, uploading, poster, mental health](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=9c3645e7-569f-4458-92ff-ad3e0080727f)

    Intro video to lab 5 covering these topics:
    
    * race announcement (see [races on the race server](https://rhul.buggyrace.net/race/), of course)
    * a reminder about [uploading your buggy data](https://rhul.buggyrace.net/users/)
    * some thoughts about [the poster](https://info-rhul.buggyrace.net/project/poster)
    * extra lab on Wednesday 9th June 09:00–12:00
    * as deadlines approach: look after yourselves and ask for help!

* [video: from the final lab: retrospective](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b52db22a-7c0c-4cd6-98d8-ad4500e9aa9f)

    This is the retrospective session from the lab on Friday morning, on the last day of term.


## Phase 0 tasks (set-up)

**Tech Notes that might help with phase 0:**

There's a note on what's going on with
[forking and cloning](https://info-rhul.buggyrace.net/forking-the-repo)
and another one about
[connecting to localhost](https://info-rhul.buggyrace.net/localhost)
(and what to do if 0.0.0.0:5000 isn't working for you).

**Videos:**

There are videos showing you how to do the tasks. Details of the command line
will vary depending on the operating system you are using.


* [video: 0-GET forking the repo](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=d81d3a9d-5ed0-4e5a-9a1b-ad33013216a3)

    Get a copy of the Buggy Editor repo onto your machine by forking it. We've
    automated this process for you: first log into your GitHub account. Then go
    to the race server, log in, click to connect your GitHub account, then
    click again to fork the code.


* [video: 0-GET using git clone (command line)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=66081520-cc38-4ef5-a40a-ad2001272186)
  
    After you've forked this video then shows the use of Git command line. The
    GitHub GUI is probably a bit easier (see the next video), but if you've
    already got Git on your machine, or prefer the command line (nice!), or
    already know Git, then this is a good way to do it.


* [video: 0-GET with GitHub Client](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=dc1be577-db16-4f23-b975-ad200135c7a0)

    There's more than one way to run Git: here's how to use GitHub client — good
    if you prefer GUIs. This is probably the best way to do it if you're not
    familiar with Git yet.


* [video: 0-GET using repl.it](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=7e3e97ef-13e3-467b-a69a-ad2000eff9ab)

    If you can't get git to work on your machine ask us for help. But if all else
    fails it is possible to work on the Buggy Editor in the browser, using
    repl.it.

* [video: 0-GET by downloading the zip](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=a0110277-1fac-4ab1-ac82-ad2401613ab4)

    Using Git isn't a requirement for CS1999, although we recommend you try it.
    The simplest way to get the Buggy Editor source code onto your machine is to
    download the zipfile from your GitHub repo... and unzip it.

* [video: 0-GET and 0-RUN with Git Bash (plus git bash tips!)](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=6f7d98ff-1c0a-41c8-b773-ad26008e0394)

    There's more than one way to run Git: here's how to use Git Bash on a Windows
    machine — including how to navigate to your folder.

* [video: 0-RUN](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b355bae4-5bed-4d31-853d-ad20011b1e47)

    How to run the webserver which is the Buggy Editor.

* [video: 0-RUN with venv](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=3ba7bb3b-0349-4297-890a-ad20011f3396)

    Ideally, use a virtual environment when you run your Python.

* [video: 0-CHANGE](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=b82ac5c3-991e-4905-9fcb-ad23015afc02)

    One way to change a template and see the difference in your browser.

* [video: database errors](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=0fc1af57-cb02-4d29-a9fa-ad2301613b9e)

    You are going to hit database errors: that's what the `try... except` blocks
    in your Python are for — and you'll see `error in update operation` a lot. :-D
    The "easiest" way to generate this error is to try to run your buggy editor
    without a database at all (whoops!). This video shows you what that looks
    like, and where that message is being generated in the source code.
    There's a useful [tech note on database problems](https://info-rhul.buggyrace.net/error-in-update) too.

## Phase 1 tasks (basic changes)

**Tech Notes that might help with phase 1:**

There are extensive notes on 1-ADD, starting with
[Identifying the template to edit](https://info-rhul.buggyrace.net/identify-template).
You might also run into problems with the CSS being cached, which interferes
with 1-STYLE: read the notes on
[static vs dynamic content](https://info-rhul.buggyrace.net/static-vs-dynamic)
and [cache-busting the CSS](https://info-rhul.buggyrace.net/cache-busting-css).

**Video:**

* [video: 1-VALID basic data validation](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=8d65c21e-1be6-435b-9c37-ad250004ff2c)

    This video shows you one way of doing the task
    [1-VALID](https://info-rhul.buggyrace.net/project/tasks/#task-1-valid),
    which should reject attempts to save buggies with bananas instead of numbers
    for wheels. It's really showing you how you are going to need to understand
    the relationship between what you see in the browser, the webserver's output,
    the templates, and the Python. Note that there are other ways of doing this
    task and this, deliberately, is not the best of them.

  
## Phase 2 tasks (refined data entry)

**Videos:**

* [video 2-RULES: violation check](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=05f88e99-f9c6-4b51-955b-ad2e017ef392)
  
    This video shows you one way into task
    [2-RULES](https://info-rhul.buggyrace.net/project/tasks/#task-2-rules),
    which should detect attempts to save buggies whose data violates rules in the
    race specification. This video almost shows you the principle behind checking
    if the number of wheels is odd (well, 3 actually). This is very similar to
    [1-VALID](https://info-rhul.buggyrace.net/project/tasks/#task-1-valid).


* [video 2-EDIT: preloading the form](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=fc19c085-f8aa-43d8-a6cc-ad2e018b3604)
  
    Here's one way to put values from the database into the form, so you're
    effectively editing it (which is what 
    [2-EDIT](https://info-rhul.buggyrace.net/project/tasks/#task-2-edit)
    is about). MDN has information on input tags
    [including the value attribute this](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#htmlattrdefvalue)
    is using.


* [video 2-FORM: adding a select tag](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=3774efc9-4dda-4bf2-a478-ad2f000745ab)

    The select tag is a better input element for some kinds of data, so is
    something you could/should do for 2-FORM. Here's the 
    [MDN information on the select tag](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/select)
    (!cute hamster alert!). At the end of the video, there's quick look at how
    this changes what you need to do for [2-EDIT](https://info-rhul.buggyrace.net/project/tasks/#task-2-edit).



## Phase 3 tasks (multiple buggies)

**Videos:**

* [video 3-MULTI part 1: update → insert](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=9911b8d3-d49d-4ba4-9d45-ad320019608f)

    Diving into task [3-MULTI](https://info-rhul.buggyrace.net/project/tasks/#task-3-multi)
    this changes the database operation from updating the single buggy you've
    been using all this time (with id=1) to inserting new records. You hit a
    little bit of SQL here which is why you should watch the video: Dave lifts
    the SQL out of `init_db.py` and uses it in `app.py`. End result: multiple
    buggies!

* [video 3-MULTI part 2: editing the record](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=bb971694-73c9-4ca3-b9e4-ad32001cc572)

    Now you've got multiple buggies you have to know which one you are editing:
    so you need to pass the id in along with the request to edit it. Obviously
    this also builds on what you did in [2-EDIT](https://info-rhul.buggyrace.net/project/tasks/#task-2-edit).

* [video 3-MULTI part 3: make vs. edit](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=c636244d-7bd3-4b90-95c8-ad32001ccb08)

    Once you've got that working you discover you've now got the distinction
    between making a buggy and editing one. This wasn't the case when you did
    [2-EDIT](https://info-rhul.buggyrace.net/project/tasks/#task-2-edit),
    because there was always that buggy. Brave new world: now you're _really_
    working with the database.


* [video 3-MULTI part 3½: make vs. edit "extra"](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=c69e7a99-1256-4f5a-b359-ad32002abcce)

    You need to change the (cosmetic, but important) title now making is not the
    same as editing. A classic example of a conditional in the template! (This
    should have been in part 3, whoops)


* [video 3-MULTI part 4: hiding the id](https://rhul.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=62a32660-b8ad-499d-a504-ad32002ec59a)

    Use of the [input type="hidden"](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/hidden)
    to tidy this up: there are hidden fields in most of the forms you submit on
    the web, and now you know why. They are not malicious, they are helping you
    by hiding what you don't need/want to edit.


## Useful links

* [GitHub](https://github.com)

    You need a GitHub account for this course (and, indeed, for CompSci next
    year). You do not need to use your college email address — so if you've
    already got a GitHub account, you can use that. Otherwise, sign up: it's
    free. Although we encourage you to use Git (version control) during the
    project, it's not compulsory — but using GitHub is, because it's how we're
    distributing the source code (and introducing you to the concepts, including
    issues). If you do already have a GitHub account, note that it does supports
    multiple email addresses, so you can add your college email if you want.

* [Flask](https://flask.palletsprojects.com/)

    Flask is the lightweight web app framework you'll be using. It's a Python
    module — you're already familiar with other modules like matplotlib and
    numpy. You might find the Flask documentation helpful. Later, if you want to
    understand the templates you're using, look in the Jinja Template docs.

* [Git (version control)](https://git-scm.com)

    We encourage you to use git during this project — that means installing it on
    your own machine. Here is the download page for installing it. Git is complex
    software, but for CS1999 you don't need to get in too deep (so it's a great
    time to start if you've never used it before). If you can't get it to
    work/install — ask for help. But don't panic, it's an extra for this course,
    not mandatory.


* [Mozilla Dev Network web documentation](https://developer.mozilla.org/en-US/docs/Web)

    The MDN web docs are a great resource — including tutorials as well as
    reference documentation:

    * [HTML elements](https://developer.mozilla.org/en-US/docs/Web/HTML/Element) (made with tags)
    * [HTML attributes](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes) (can be added to tags)
    * [CSS (Cascading Style Sheets)](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference) (for styling elements)
    * [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference) (for in-browser ("client-side") programming)

* [Python3 official docs](https://www.python.org/doc/)

    OK so you already know Python — remember FY1009? — but knowing a language
    doesn't mean you don't need the docs: it means you know how to use the docs.
    If you already know what you're doing, make sure you're following
    [PEP-8](https://www.python.org/dev/peps/pep-0008/).

* [JSON specification](https://www.json.org/json-en.html)

    JSON is a format for describing data with text (so really, it's a string).
    It's popular for passing data between programs (in our case, from your buggy
    editor into the race server) because it's not especially verbose, and humans
    can read it without too much difficulty. You'll recognise it because by no
    coincidence it looks a lot like how you described data in Python. Check out
    the [syntax diagrams on json.org](https://www.json.org/json-en.html). The
    buggy editor code in your repo already knows how to produce JSON, so you
    don't need to figure that out — but maybe you can look to see if you can work
    out how it's doing it.

* [CompSci superbasics](https://rhul-cs-projects.github.io/compsci-superbasics/)

    The CompSci superbasics were put together **specifically to help you** if
    you've never had to use a computer this far outside of its Graphical User
    Interface (point and click) before. We'll be looking at the
    [command line](https://rhul-cs-projects.github.io/compsci-superbasics/command-line/)
    a little bit more in CS1998, but for some of you this project will be the first
    time you've needed to properly navigate around the
    [file system](https://rhul-cs-projects.github.io/compsci-superbasics/file-system/)
    too. Start here if you're finding it tough... and ask for help!



