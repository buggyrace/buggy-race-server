

# 0-CHANGE

## Make a change to a template and see it appear

### Problem

You must demonstrate that you can change a template so the change appears in
the browser.

### Solution

Edit some text in a template (e.g., `templates/index.html`).
Confirm it changes when you hit the corresponding page in the browser.

### Hints

* This is just a "smoke test" of your change process: before you try to do the
  complex tasks, like changing the behaviour of the web app, do something simple
  to confirm that the templates really are being used the way you think they
  are.
  
* It's also a good sanity check that you're editing the right file (and indeed
  repo).

* If you change the template but the page in the browser does not change when
  you refresh it... what might be happening? What can go wrong here?

* If you're using version control (git) — we encourage you to, but it's not
  mandatory — of course you should commit this change. This is also a simple
  end-to-end check that your Git is set up OK.

* Don't underestimate the importance of doing a simple test before doing complex
  ones!


# 1-TEMPLATE

## Add a new template to the app

### Problem

Some useful information — such as the cost of buggy components — is only
available on the race server. You can't access this information when you're
using your buggy editor offline.

### Solution

Add a new page called `/info` that displays the cost information.
Now you (or any user of your buggy editor) can investigate buggy costs without
going to the race server.

### Hints

* Implement this by adding a new template (`templates/info.html`) which your
  app will render when `/info` is requested.

* Your webserver uses the _route_ to choose which function to run to generate
  the response: in `app.py` this usually renders a template, which results in
  the HTML that is sent back to the client (browser). In this case you want
  a route that matches `/info` to render the template `info.html`.

* You can copy the information you need from the race server and put it into
  the template. It's fine to do it by hand (although there are other approaches
  too).

* Maybe you should include the date you did this too. Why?

* It's up to you What data from the specs do want to display. Maybe you can copy
  the whole page. Or maybe you can be selective. Do you think you should include
  a link to the specs page on the race server?

* Putting data (for example, the cost values for different fuel types) directly
  into the HTML template is called *hard coding* it. What are the disadvantages
  of hard coding data like this?

* You might choose not to hard code the values in your template: another place
  you could put them is inside `app.py` and then pass them into the template.
  What advantages does this approach have?
  
* You could put the data in a data file and have your server read it, and
  pass the data to the template when it renders it. This is probably a better
  solution to hard coding values in Python or the template — why? If you do it
  this way, you need to decide _when_ to read the file; your decision will
  depend on how efficient you need your program to be.

* This task is good preparation for adding your [poster](/project/poster).

# 1-ADD

## Add more data to the form

### Problem

The only data being collected by the form is the number of wheels.

### Solution

Add more items to the form (and save it in the database).

### Hints

* **You do NOT have to add all the items for the buggy here: just something in
  addition to "wheels"**. Eventually, ideally, yes: but to start with, just
  see if you can add one item. We suggest: the **colour of the flag**.
  That's a good one to start with because _it's already in the database_.
  
* You'll have to add each item to the form and the method on the server which
  processes it.

* You'll need to update the SQL too that saves it in the database: look at the
  database definition in `init_db.py` to see the column name (and type) for
  each item. This is tricky! **See the CS1999 tech notes!**

* Look at how the existing code does it for the number of wheels: the pattern
  will be the same.

* Not all elements in the form should use input tags. Investigate other HTML
  tags for accepting data in forms: in particular, consider how radio and
  select might help you.

* We **strongly recommend** you add each new datum **one at a time** (not lots
  in one go). (If you're using version control, each one should be a commit).
  Why?


# 1-VALID

## Add basic data validation

### Problem

If you enter "banana" for the number of wheels, you should get an error.

### Solution

Add data validation: you app should check that the data input is the right kind
of thing (an integer) and reject it with a warning.

### Hints

* The incoming data is always a string, so maybe use the `isdigit()` method.

* Do you need to "clean" the string first? Python has a `string.strip()` method
  which strips off all leading and trailing spaces

* What are you going to do if the data is bad?

* There's more than one way to pass the error back to the user... how are you
  going to do that? What should appear on the webpage?

* We expect you to implement this in Python (that is, server-side validation).
  But you can do client-side validation in JavaScript as well. What's the
  difference? Why isn't _only_ using client-side JS acceptable?

* Unless you've changed it, the editor is using SQLite as its database, which
  has a non-standard quirk: in fact you can store text in integer fields (this
  is obviously problematic!) Other SQL engines will throw an error here! You
  can explicitly add an integer check in the database's SQL with
  `CHECK(typeof(qty_wheels)='integer')`... or switch to a more powerful
  database engine.


# 1-STYLE

## Style your editor just how you like it

### Problem

Your editor looks identical to the basic one.

### Solution

Make it look beautiful and different from everybody else's.

### Hints

* Use [Cascading Style Sheets (CSS)](https://developer.mozilla.org/en-US/docs/Web/CSS)
  to make these changes.

* You can change the HTML as much as you need to get the look/layout you want,
  but be careful — remember the _separation of concerns_. This means your HTML
  should really only be describing the **content** of your web pages, while the
  CSS deals with its **presentation**. It's common to use the `class` attribute
  as the bridge between the two.

* You editor is already using a style sheet — it's in `static/app.css` — so
  you should probably edit that (at least to start with).

* If you make changes to the stylesheet but your browser doesn't appear to
  load it (but keeps using the old one) you _might_ need to empty your 
  browser's cache.  **See the CS1999 tech notes!**

* If you want to add images, those should probably go in the `static`
  directory (the same place as the CSS). Make sure the file size of any images
  is as small as possible. Why?

* No matter how pretty, how beautiful, how fabulous you make your editor, 
  remember that you **must not** compromise its usability or accessibility.

* For example, never put text directly on top of backgrounds that make it hard
  to read or distinguish. Make sure _things the user should interact with_ look
  different from things they cannot. Consider how your site works in different
  [form factors](https://en.wikipedia.org/wiki/Form_factor_(design)).

* There are guidelines for calculating
  [acceptable contrast](https://developer.mozilla.org/en-US/docs/Web/Accessibility/Understanding_WCAG/Perceivable/Color_contrast)
  between text/background colour combinations.

* **Accessibility is a big topic that is integral to web design.** See
  [MDN on accessibility](https://developer.mozilla.org/en-US/docs/Learn/Accessibility)
  for a good starting point. If you have any aspirations as a web developer,
  you have professional, ethical, and legal obligations to understand how to do
  this well.


# 2-EDIT

## Edit the record by loading its current values into the form

### Problem

In the basic app, the form is blank when you visit it so it always implies the
default value.

### Solution

Before you present the form, you should fill its values with the current
settings from the Buggy record in the database.

### Hints

* You need to read the values for the existing buggy record out of the database
  with `SQL SELECT`.

* Use the `value` attribute of the HTML's `input` tag.

* You'll need to handle `select` tags' `option` values differently: you'll need
  to use the selected attribute too.

* Be careful about values that might contain characters that break your HTML
  when you put them inside attributes in your template. How can you protect
  against problems?


# 2-FORM

## Make the form better

### Problem

The basic form isn't easy to use. Can you make it better?

### Solution

Try to lay out the form to be clear and easy to use.

### Hints

* Maybe add hints or guidance for the user.

* How does the way a form is laid out affect how easy it is to use? Can you
  line the inputs up? Does it matter?

* Investigate the HTML `label` element and its `for` attribute.

* How can you change the way errors are displayed?

# 2-COST

## Calculate and save the game cost of the buggy

### Problem

The cost of the buggy (worked out using the game rules) affects whether it can
be entered in some races. Add the cost to the record.

### Solution

Add a new integer column called `total_cost` to the `buggies` table, and store
the total cost there.

### Hints

* You'll need to load the cost data. How difficult is it to get that data? What
  would be the easiest way to provide that data for you?

* You probably already copied some (if not all) of this cost data from the
  race server when you did [task 1-TEMPLATE](#task-1-template).
  How can that help you with this task?

* You can hard code the costs directly into your source code... this is OK,
  but it can get tricky mixing data and code. What other ways are there to do
  this?

* What happens if the costs (the data) change up on the server? How would you
  notice?

* _When_ do you need to calculate the cost of the buggy?


# 2-RULES

## Add validation according to the game rules

### Problem

There are some configuration options that are not allowed (for example,
the quantity of wheels must be even).

### Solution

Add game rules to your validation.

### Hints

* You'll need to be certain what the game rules are.

* You'll probably need to do some validation based on more than one field too
  (for example the number of tyres cannot be less than the number of wheels).

* How and where are you going to report the problems?

* Do you save the record anyway, even if there are violations?

* If the game rules changed, what would you need to do to your program?

# 3-ENV

## Switch between dev and production environments

### Problem

When you run your editor, it's _always_ in debug mode (because the keyword
argument `debug=True` is being set when `app.run()` is called, at the
bottom of `app.py`). But debug mode should only be enabled when you run
your editor in a development environment.

### Solution

Change your program to use the environment variable `FLASK_DEBUG` to switch
debug mode on and off, instead of being hard-coded (i.e., explicitly set in
the source code).

### Hints

* There are two meanings of "environment" being used here: the general
  environment ("development" where you are making changes to your program, and
  "production" where you are using it), and the technical environment in which
  the program runs... but they are related.

* In practice the main advantage of switching between development and
  production environments in Flask is that in the development environment the
  webserver should "notice" (and reload) changes to the files, so you don't
  need to stop-and-start the webserver every time you make an edit. But it also
  affects the way errors are displayed in the browser — Flask's debug mode will
  show a stack trace and detailed diagnostic information, instead of a bare
  [status-code 500](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500)
  error page.
  
* This task is really introducing you to the important concept of
  [environment variables](https://en.wikipedia.org/wiki/Environment_variable)
  — these are settings that are part of the environment in which the program
  runs instead of being inside the program. All general programming languages
  provide a mechanism for accessing these from within the program's source
  code. In Python, you should import the `os` module and use its `environ`
  methods: see the [Python environ docs](https://docs.python.org/3/library/os.html#os.environ).

* The environment variables are effectively presented to your program as a
  dictionary of string values (be careful: even the ones that look like
  numbers or Booleans are really strings, so you might need to cast them).
  Although you can access environment variables directly by keys in `environ`
  (such as `os.environ['FLASK_DEBUG']` for the environment variable
  `FLASK_DEBUG`) it's usually better to use `os.getenv('FLASK_DEBUG')`. Why?

* Environment variables are managed differently on different operating systems
  (which makes sense, since it's those systems which control the environment in
  which your program is running). So Windows and Unix/Mac set them differently
  (see below).

* You can also choose to have **different databases** depending on the
  environment — this means you can test your code in development without
  risking damaging your best buggy data in the production database. That is:
  you do your coding and hacking in your dev environment, but switch to run in
  production environment when you just want to edit your buggy.

* If you want to implement switching between different databases, you'll need
  to change how the constant `DATABASE_FILE` is set in `init_db.py` and
  `app.py` (it can't simply be the same filename — instead you'll need to use a
  conditional). You don't need to do this database-switching for 3-ENV, but
  it's great if you do (because it's a very handy technique to know when you
  are a developer!).

* You probably need to use `set` (Windows) or `export` (Unix/Mac) — although on
  Unix/Mac you can also declare environment variables when you run the command:
  `FLASK_DEBUG=True python3 app.py` (but... be careful about how you use that
  value inside your program — is it a string or a Boolean value?)

* Another way is to make a `.env` file and `pip install python-dotenv`. What
  does that do?

* The **three classic environments** are _development_, _staging_, and
  _production_ (you can think of _staging_ as _testing_).

* Setting `debug=True` in the source code is just one example of how some
  settings should not be hard-coded. Other classic examples, for programs
  in general, are configuration settings and passwords. This is really about
  understanding what is the same and what is different when you run different
  _instances_ of your program. This is especially important when you think
  about how source code is shared, and what should (and should not) go into
  version control.

* It's a good idea to document how the environment can be used to control the
  behaviour of your program in the `README.md`

* This can be quite a complicated topic, because configuration is a big deal
  when you're writing programs for other people to run. See the Flask docs about
  [configuring from environment variables](https://flask.palletsprojects.com/en/2.3.x/config/#configuring-from-environment-variables) to see what's possible.

* This task might not result in much new Python, because it's really about _how_
  you manage your development environment. Make a note of what you did, because you
  can describe this in your
  [%PROJECT_REPORT_TYPE%](%BUGGY_RACE_SERVER_URL%/project/%PROJECT_REPORT_TYPE%).
  In fact it's possible that the only change you make to `app.py` is to _delete_
  some code...


# 3-AUTOFILL

## Add auto-fill to the edit forms

### Problem

After you've made your some choices on your buggy form, there are still lots of
items to fill in. It would be good to auto-populate empty settings with values
that create a complete, viable buggy.

### Solution

Add a button that automatically fills the other entries. Maybe these are just
sensible default values. Or perhaps you can ask for a cost limit when the button
is pressed, and try to add items so that the buggy's total cost is within that
limit.


### Hints

* You can do this server-side (with Python) or client-side (with Javascript) —
  why is this suitable for client-side? What difficulties does that introduce?

* You might need to randomly choose values: see Python's `random` library and
  perhaps its `randint` function (or JavaScript's `Math.random()`).

* Maybe you need a way to decide which fields should be filled — perhaps empty
  fields. How can you tell which fields those are?

* If you try to make autofill work within a specified cost, this can become a
  very difficult problem. How do you decide what values to pick for each
  setting? Sometimes it might be _impossible_ to make a legal buggy within the
  stated cost. How will you know? How will you report that to the user?

* If you don't try to make autofill work within a cost, this task is a lot
  simpler — then it's really just loading default values. That's not so helpful
  for the user though.

* If you are randomising legal values, after you've done it one, will it work
  again? (Not if you are only populating empty fields). Should you provide a
  button for clearing all the inputs? Or simply filling _all_ of them?


# 3-MULTI

## Allow different buggies to be created

### Problem

The default app only lets you save **one buggy**. You should be able to save
different buggies so you can switch between them.

### Solution

Modify the app to create a new buggy and subsequently update it, and to provide
a way to switch between the different buggies you've created.

### Hints

* This is part of the classic set of
  [CRUD operations](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete):
  it is not a small change.

* Note that we've moved _deleting_ into a [separate task (3-DEL)](#task-3-del).

* You'll also need to manage a way to select which buggy you are editing or
  deleting — offer a list to choose from, perhaps?

* You're going to need to change the operation on the database, because up
  till now you've been _updating_ the (single) record in the database: now
  you will sometimes be _inserting_ a (new) record. How will you decide which
  to do?

* When you create a new buggy, it will be given a new `id` because the database
  assigns an auto-incrementing integer. How do you determine what that `id`
  was? Why does it matter?

* Once you've created a buggy, you'll need to specify which buggy a request
  relates to... you do that in Flask by incorporating its `id` into the route.

* If you need help with the SQL to get the database operation to work, ask
  for help (SQL is not a one of the core components of this project).


# 3-DEL

## Allow buggies to be deleted

### Problem

You have multiple buggies: you should be able to delete ones you don't want.

### Solution

Add a `delete` route to remove a buggy.

### Hints

* This is one of the
  [CRUD operations](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete):
  see the [mutliple-buggy task (3-MULTI)](#task-3-multi) too.

* You should put the `id` of the buggy you're deleting in the route.

* You almost certainly need to use the `WHERE` clause in your SQL. What happens
  if you don't?

* It's good practice to use the HTTP method `DELETE` here (or perhaps `POST`...
  but `DELETE` is better).
  
* More importantly, you **should not use** the HTTP method `GET` for this route.
  Why not?

* Have you just made it possible to delete _all_ the buggies? Is that OK? Does
  your editor still work if you do?

* Does this change anything about what `init_db.py` should do?


# 3-FLAG

## Display the pennant graphically

### Problem

The user's choices for the colours and pattern of the buggy's pennant (flag) is
visual information but is probably displayed as text.

### Solution

Show a graphical representation of the pennant in the browser.

### Hints

* There are several of ways of doing this: but you can't simply have
  pre-prepared graphics for every possible flag because there are too many
  combinations.

* Are you going to display the pennant before or after the form is submitted?
  (Both are OK... but what difference does your decision make? Is this
  client-side or server-side?)

* There are number of ways you might go about implementing this without needing
  to create a separate image file (which we recommend against). Consider using
  CSS, SVG, or canvas to paint the flag (a small rectangle would be fine). What
  are the pros and cons of the different approaches?

* Remember that the colours are specified in a very specific way: as
  [CSS colours](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value).

* What happens if a colour has been badly specified? Is it dangerous to try
  to display it?


# 3-TESTS

## Write some tests

### Problem

You should be able to run automatic tests that confirm your app calculates the
cost correctly... as well as other things too.

### Solution

You probably know your app works because you've been running it (and playing
with it) as you go along. But you should write some _automated_ tests.

### Hints

* Testing is a _big_ topic!

* The idea is that you can run the _same_ tests repeatedly, and get the same
  results every time. This way, if you make any changes to your code — adding a
  new feature, for example — you can be confident it does what you intended it
  do and it _doesn't break anything that is already working_.

* There are two common types of tests: _unit tests_ and _integration tests_.

* _Unit tests_ are used to check that single, individual operations do what
  they should.

* _Integration tests_ are used to check that things are working together
  properly.

* Python has the `assert` keyword for writing tests.

* Python has some libraries to make it easier for you to write tests:
  investigate `unittest`, `nose2`, or `pytest`.

* For example, the `unittest` library provides more methods like these:
  `assertEqual`, `assertTrue`, `assertFalse`, `assertIs`, `assertIsNone`,
  `assertIn`, `assertIsInstance`...

* What different _kinds_ of test are appropriate here?

* Testing the front end (i.e., the interface behaviour in the browser) is
  harder, but it can be done. What tools are available for testing.

* Even if you don't have any automated tests, you can describe a set of tests
  that you (or a tester) can run through manually to show your editor works.
  You can present testing instructions — your manual test suite, and
  instructions for executing any automated tests you've written — in a file
  called `TESTING.md`.

* Consider which tests are _worth_ testing: be smart and effective with your
  _choice_ of tests.

* The classic set of testing criteria are: none, one, and many. How does that
  apply to your tests?

* If you are using PyCharm or Visual Studio Code, you'll find there is
  support built-in to help you write and run tests.

* If an application contains tests, it is common practice to include
  instructions in the README which describe how to run them.


# 4-API

## Use the server API for submitting the buggy data

### Problem

Manually copying the JSON data from the editor to paste into the race server is
clunky — use the buggy submission API instead.

### Solution

Ask for the API specification and implement an **upload to server** feature for
a selected buggy.

### Hints

* The API isn't published: we'll provide it when you need it.

* You'll need some way of storing information about the server (including
  authorisation criteria) — maybe where/how to set config is related
  to the way you managed the email settings needed for
  [resetting passwords (5-RESET)](#task-5-reset)?


# 4-USERS

## Add users (and sessions) so you know who is editing a buggy

### Problem

Anyone can access your app and edit a buggy: ultimately only the person who
created it should be able to. Add a login mechanism so you can tell the
difference between users.

### Solution

Add usernames to distinguish between users, and a mechanism for starting and
ending a session (such as logging in and logging out).

### Hints

* This task is really about implementing _login sessions_. See also
  [make a new user (4-REGISTER)](#task-4-register) and
  [add passwords (4-PASS)](#task-4-pass), which are related.

* It is possible to implement user sessions _without_ having any users in the
  database: just by inviting the user to type _any_ username and keeping that
  for the session (that is: you _could_ implement this without a database).
  That is, 4-USERS is really about starting, maintaining, and ending a session.
  Here's the
  [official Flask example](https://flask.palletsprojects.com/en/1.1.x/quickstart/#sessions)
  that implements that.

* The most common way sessions are implemented is with _cookies_, which are
  tokens the server can use to recognise when requests are coming from the
  _same_ client (browser). That's how Flask is doing it too. If you use your
  browser's developer tools to find the cookies, you can see how they change
  between requests as you use your app.

* Remember to provide a way to end a session as well as starting it.

* To get this working with a database, add a table called `users` and manually
  create users directly in that (or maybe create them in `init_db.py` or a
  script like that). But see the
  [new-user task (4-REGISTER)](#task-4-register) for doing it from _within_
  the app itself.

* See the [new-user task (4-REGISTER)](#task-4-register) task for more
  hints about the user table in the database.

> There is a library called `flask-login` that can you can use — but we think
> that is overkill for this project — it's probably better (and more
> interesting) to build your own simple login mechanism.
> 
> To be clear: `flask-login` can solve this problem, _but_ it comes with quite
> a lot of extra dependencies and complexities. If you've used it before,
> you're welcome to dive in with `flask-login` if you want... but it's
> certainly not a requirement.

# 4-REGISTER

## Make a new user

### Problem

Make it possible to create a new user to use when logging in with 
[user logins (4-USER)](#task-4-user).

### Solution

Make a registration (or sign-in) page with a form for creating new users.


### Hints

* The page presumably needs to collect information needed for the user
  record. What fields do you need?

* If you were going to run your editor as a service — that is, genuinely
  invite people to register as users — you would need to be aware of your
  responsibilities under the 
  [UK GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/).
  If you collect information about individuals for any reason other than your
  own personal, family or household purposes, you need to comply with the GDPR.
  That basically means you declare what personal data you collect, what you
  will use it for, and that you must keep it safe.

* You can register users without any additional authentication. In this case
  maybe you _also_ grant them a login session as soon as they have submitted?

* If you collect email addresses, how can you verify that they are valid, and
  belong to the person who is using your editor?

* It's common to use a table called `users`.

* If you're using SQLite in development mode, you'll probably need SQL to
  `CREATE TABLE users` with an auto-incrementing primary key `id` and string
  (`VARCHAR()`) field `username`

* What's the advantage of using an `id` as the primary key instead of the
  `username` (after all, you know `username` has to be unique)?

* What happens if someone tries to register a user with a username that
  already exists? How would do you know this has happened?

* If you're thinking about passwords too, we've added that as a
  [separate task (4-PASS)](#task-4-pass). If you're coding this from scratch,
  it might be a good idea to implement user and session first and then add
  passwords (why?).


# 4-OWNER

## A buggy belongs to a user

### Problem

Any user can edit any buggy. Only the buggy's creator should be able to edit
(or delete) it.

### Solution

Associate buggies with a specific user and only grant access to buggies to the
logged-in user.

### Hints

* Maybe add a `user_id` column to the buggies table for the user's id — this
  is a *foreign key*.

* Ensure you use the foreign key in the `WHERE` clause of `SELECT` statements.

* Remember to always set the `user_id` column when you create new buggy records.

* Should `user_id` appear in the HTML `form` when creating a buggy? What about
  when editing it? Perhaps you could use a `type="hidden"`? What's the problem
  with that?
  

# 4-PASS

## Add password protection to the users

### Problem

Anyone can login as any user they like... unless there is a password on user
accounts.

### Solution

Set and store a password for each user.

### Hints

* You need to add password checking to part of the login process.

* You must not store the password in plain text. Why not?

* You'll need to hash the password: we recommend using Python's `bcrypt`
  library.

* Login verification means hashing the guess and comparing that with the stored
  value of the hashed password. If the values are the same, the guess was
  correct.

* You should hash your passwords with a _salt_. What's a salt? Why is it
  important? What attack is it preventing?

* We've required passwords for this task — but there are other ways of
  implementing access control, and passwords have some weaknesses.

* What's the difference between authenticating a user or authorising them?


# 5-VIZ

## Visual representation of the buggy

### Problem

The buggies are just a bunch of numbers and settings!

### Solution

Construct a visual representation of each buggy that shows its configuration.

### Hints

* This is presumably client-side using JavaScript. You can draw shapes
  natively, but it's a lot of work: there are a number of drawing libraries so
  we recommend you use one of those.

* Although it's _presumably_ client-side... could you do this server-side, with
  Python? How might that work? What are the pros and cons of this approach?

* The two common ways of drawing in the browser are canvas or SVG.

* This is potentially — by far — the most complex of the tasks. What are the
  limits? A 2D rendering of a 3D model? Downloadable files for 3D printing?

# 5-RESET

## Password reset

### Problem

A user who forgets their password can't log in.

### Solution

There's no email address associated with a user, so to implement a reset
password option perhaps you'll need to add that to the user record, and find a
way to send an email from within Python. Or use a one-use token system (see
hints).

### Hints

* See also the [admin user (5-ADMIN)](#task-5-admin) task, which potentially lets
  an admin fix this instead. Why have password reset if you have an admin user?

* In order to send an email, you'll need to connect to an SMTP server. So
  you'll need to know details for that server (including, probably, some
  authentication criteria such as username and password). How will you make
  that information available to your program? Why should you _not_ put it in
  the code (or _any_ of the files in the Git repo)?

* If you don't want to implement email — which is a whole subsystem _just_ to
  reset a password — you could implement a token system instead.

* A token system lets an [admin user (5-ADMIN)]{#task-5-admin}) add a token
  to a user's record. The admin then tells the user what the token is. The token
  should also have a time-limit. If the user goes to the _reset password_ page
  and enters the token before it has expired, their new password is applied.


# 5-RACELOG

## Store a history of race results for the buggies in your app

### Problem

You don't know how well different buggies did in their races, but you should
be able to see which ones have won more races, and how.

### Solution

Store and present a log of race results for each buggy.

### Hints

* How are you going to get the data? In what format(s) does the race server
  make this data available? Which would be easiest for you? Why?

* There's no table in the database for this, so maybe you'll need to add one,
  perhaps with SQL's `CREATE TABLE`.

* But you'll need to design the table too and think carefully about what
  columns you need.

* Which columns can be `NULL`?

* What's the best data type for storing when the race took part?

* How are you going to connect the records with the specific buggies?

* What happens if a buggy is deleted after the race results have been stored in
  your database? What are the various remedies to that?

# 5-ADMIN

## Add admin capabilities to superusers

### Problem

At least one user should be able to change other users (and admin, or
superuser).

### Solution

Use something like the `is_admin` setting in the users table and add superuser
capability for manipulating buggies and users.

### Hints

* The `flask_login` library already has the concept of admin users but if
  you've implemented your own users (which is great!) you need to add a
  way of determining whether a given user is indeed an administrator. 

* The `is_admin` column in the users table should be set, so you can check
  in your python if the `current_user` has superpowers.

* The superuser should have CRUD on other buggies... and other users.

* Some frameworks ship with the capabilities to autogenerate admin back-ends
  like this. What about Flask? Are there libraries available that do this for
  you?

* How do you create a new admin user?

* How about changing `init_db.py` so it _creates_ an admin user when the
  server is first installed? What would you have to do to make this work?
  What mitigations could you put in place to minimise any risks that might
  arise from having an initialised admin user in the database?

* What happens if you delete the only remaining admin user? What's a design
  solution to this?

# 6-FREE

## Add custom features to the editor

### Problem

This task is a freestyle placeholder for other developments to the editor
once you've done all the others.

### Solution

Implement your own custom features.

### Hints

* Limitless :-)





