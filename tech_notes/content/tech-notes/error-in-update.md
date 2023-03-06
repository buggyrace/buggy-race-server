Title: error in update operation


# "error in update operation"

---

## Or: problems saving to the database

This is the error message you get when there is a problem saving your buggy to
the database. You see it (and not a Flask error page) because `app.py` contains
a `try` block which contains the code that executes the update. Any error that
occurs in that block will trigger the `except` block, which sends that message
(`msg`) out into the `updated.html` template.

> If you want to see the actual error message, change the `except` block in
> `app.py` with the code at the [↓ bottom of this page](#how-to-show-the-error).

## What's gone wrong?

If _anything_ goes wrong inside the try block, you'll see this error.

It's often one of these things (see below for details on each one):

* [↓ missing database](#missing-database)
* [↓ unknown SQL column name](#unknown-sql-column-name)
* [↓ wrong number of `?`s in the SQL](#wrong-number-of-s-in-the-sql)
* [↓ syntax error in SQL (#trailing-comma?)-↓](#syntax-error-in-sql-trailing-comma)
* [↓ number of Python variables doesn't match number of ?s](#number-of-python-variables-doesnt-match-number-of-s)
* [↓ bad Python variable name](#bad-python-variable-name)
* [↓ Python syntax error](#python-syntax-error)

### Missing database

Remember you have to run `init_db.py` to create the database. If you _have_ run
`init_db.db` but you cannot see a file called `database.db` in the same
directory, maybe it's not in the same place as wherever `app.py` is running.
(Have you got a copy of your project somewhere else? Whoops.)

### Unknown SQL column name

Every column name in the SQL statement must match what's in the database.
Column names are what appear in the `CREATE` statement in `init_db.py`. We'd
expect those to be the same as the JSON names for the inputs that appear in
the [buggy spec]({{ BUGGY_RACE_SERVER_URL }}/specs/).

* did you spell it right? (`flag_color` not `flag_colour`)
* if you added a new item, you probably remembered to add it to `init_db.py`.
  But did you **delete the database** and run `init_db.py`?
  See the tech note on [adding new data](adding-new-data-i).

### Wrong number of `?`s in the SQL

SQL maps each `?` into a value to store/use in the column. This is especially
fiddly with the `INSERT` statement. You must have the right number of `?`s. If
you're even one out, it's an error. Ouch.

For example: two columns (quantity of wheels and flag colour) need two `?`s:

```sql
INSERT INTO buggies (qty_wheels, flag_color) VALUES (?, ?)
```

### Syntax error in SQL (trailing comma?)

Syntax errors in your SQL mean your attempt to save to the database will fail,
of course. **The focus on this project is the Python, not the SQL** so if
you need help with the SQL, ask us!

The most common error is this trailing comma immediately before the `, WHERE`
(that comma should not be there).

Wrong:

```sql
UPDATE buggies set qty_wheels=?, flag_color=?, WHERE id=?
```

Right:

```sql
UPDATE buggies set qty_wheels=?, flag_color=? WHERE id=?
```

The same trailing comma can catch you out in the `(...?, ?,)` in `INSERT`
statements too. There should _not_ be a comma before the final `)`.


### Number of Python variables doesn't match number of ?s

When you update the database, Python is calling the SQLite module's `execute()`
method with two arguments. The first argument is a string containing the SQL
instruction, and the second is a list of values to use (in your case that's
almost certainly a list of variables).

* are there _exactly_ as many variables in that list as there are `?`s in the
  SQL?

* if there is only one single variable, it _must_ be a list

   This special case is a bit horrible: if you really do only have one single
   variable, you need to present it _with_ a trailing comma like this:
   `(thing,)` not `(thing)`. This is to _force_ Python to understand that
   you're sending a list even though it contains only one thing (without the
   comma, the parentheses just describe grouping).


### Bad Python variable name

If you've made a mistake (a typo?) with one of the variable names, Python will
complain that you haven't declared the variable. (It therefore knows this
variable cannot have a useful value, so you can't have meant to do this).
Normally you'd see the Python error and a line number, but _this_ has happened
inside the `try` block so you don't.

If you have a lot of variables (you might do if you've populated the whole
database table), one "quick" test here is to copy-and-paste the list into a
`print(...)` statement just before the `try` block starts. You don't care about
the output but you know if there are any undeclared variables there, Python
will blow up with an error. (If you do this, remember to delete the test line
after you've run it).

### Python syntax error

Finally, this is similar to the bad Python name but harder to check. If you
have a Python syntax error, it could be triggering the `try` `except` behaviour.
If you can't spot it, try the technique of limiting what errors the `except`
shows (for example, by using `ZeroDivisionError`) described below.

---

## Put as little code inside the `try` block as possible

When you add new Python (for example, testing values from the form for
[1-VALID]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-valid)) don't put it inside
the `try` block unless it's part of the SQL operation. If you do, and it's got
an error (you spell `flag_color` with a `u`, for example), instead of seeing
Python's specific message about not recognising `flag_colour`, you'll just get
"error in update operation".

So keep as little inside `try` blocks as possible.


## Why is this error message different from the rest?

If you're running in Flask's debug mode (which `app.py` sets for you with
its very last line), you're used to seeing error messages (and stack traces)
from Flask and Python.

But this is different because it's catching it in the `try` block. Why?

Well, this is very common on webservers because it means if there is an error
the user gets _told_ something went wrong but still gets a useful web page —
instead of a "stack trace" and error message (or just "error 500"). This
means there are still buttons to click on. You've almost certainly experienced
the difference on websites you've been on when they have encountered errors.

The catch is, when you are the developer, it's hiding the information you
want.

One way to see that information is to remove the `try` `except` `finally`
entirely, by moving the SQL code outside of it. You know that can work because
the other SQL operations in your `app.py` are not inside the try/except block.

## How to show the error

A better way is to use the `try` block to catch the error, but then extract the
error in the `except` and show it in the `msg` you pass back.

Do that by changing the `except` block in `app.py` to include the exception too,
like this:

```python
        except Exception as error:
            con.rollback()
            msg = f"error in update operation: {error}"
```

This works because putting the exception (`error`) into the format string (the
"f-string") _casts_ it into a string (i.e., forces it to be a thing of class
String, instead of Exception). The string form of an exception is the (hopefully
helpful) error message that it is carrying.

