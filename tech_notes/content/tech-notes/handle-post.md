Title: 1-ADD handling POST


# Handle the POST request

* Task [1-ADD add more data to the form]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add)

---

Now you have the form `POST`ing the data to the webserver you have to
handle it with Python.

You know where this is being processed: the route (action) and method was
explicitly specified by the `<form>` tag.

So follow the same pattern that is already in place for the `qty_wheels`.

Here's the existing code. Not all of it is relevant, but that's part of the
skill of learning to read code. 

```python
elif request.method == 'POST':
  msg=""
  qty_wheels = request.form['qty_wheels']
  try:
    with sql.connect(DATABASE_FILE) as con:
      cur = con.cursor()
      cur.execute(
          "UPDATE buggies set qty_wheels=? WHERE id=?",
          (qty_wheels, DEFAULT_BUGGY_ID)
      )
      con.commit()
      msg = "Record successfully saved"
  except:
    con.rollback()
    msg = "error in update operation"
  finally:
    con.close()
    return render_template("updated.html", msg = msg)
```

## First, understand the existing code

You need to look at that while thinking about how it's handling the data
you _do_ know works: `qty_wheels`.

The Python is initialising a variable called `qty_wheels` to contain the value
of `request.form['qty_wheels']`. That's how the data from the `<form>` tag is
being presented through the request — in fact, the Flask library is doing the
work there and it's Flask that has made `request.form` for you.

The next place that's doing something with `qty_wheels` is `cur.execute("UPDATE
buggies...)` If you have a poke around in that code you should see how `cur` is
related to `con`... and `con` is the name given to `sql.connect(DATABASE_FILE)`.

So this is where the buggy is bring written to the database. That should be
what you expected because that's what this `POST` request from the form was
supposed to be doing anyway.

An important point here if you're new to programming is that you _can_ make
some sense of this even though you probably wouldn't have been able to write it
all from scratch.

### Python does try

The `try`, `except` and `finally` are all Python's mechanism for trying to
do something, coping if it goes wrong, and then tidying up at the end regardless
of whether or not things went well.

Why might it go wrong? Because writing to the database is an operation that is
passing control over to another service (in this case SQLite) and a whole new
world of problems can exist: Python is actually using another language — SQL
— to communicate with it, and there might be errors in that. Or the connection
to the database might not work.

## Second, investigate the msg code 

There's a variable in this code called `msg` that you should try to figure out.

You can see from the `except:` line that "error in update operation" is being
put into variable `msg`.

However, if the update went OK, you can see `msg` gets a success message
instead.

Where's `msg` being used? It's being passed into the template `updated.html`.

So the next thing is to quickly look in that and see what the template does
with it. Can you see how `msg` is used in 
[that template]({{ BUGGY_EDITOR_GITHUB_URL }}/blob/main/templates/updated.html)?

Why is `render_template()` being called at all? The answer is that although
the browser sent data to the server to be added to the database, that is still
an HTTP request, so it needs a response... and that response is the HTML page
it will show. So `updated.html` is sent back to the browser and the browser
will display it — thereby reporting the success or failure of the attempted
operation.

### Send a message back to the browser

Before you add the new code: do this test.

Now you know that `msg` is a string which is shown on the page that is sent
back to (and hence displayed by) the browser, you can use that to show debug
information too. If you comment out the success message and add an
extra line like this, and then submit your form, what do you see in the browser?

```python
# msg = "Record successfully saved"
msg = f"qty_wheels={qty_wheels}"
```

You should see `qty_wheels=4` (or whatever you put in the form). That
information is doing a round trip: the browser is sending the `qty_wheels`
number in as a (named) datum in the form, the Python is extracting it, putting
it in a message, and passing it back — via the template — to the browser.

## Now grab the flag colour and check you've got it

So now you can make the variable:

```python
flag_color = request.form['flag_color']
```
...and if you put _that_ into the `msg` string, can you confirm that you
are collecting it correctly by passing it back in the message through the
`updated` template?

Note what has happened here: you've made a variable called `flag_color` and
used it to extract the item from the form that was also called `flag_color`.
You _could_ call your variable anything your like, e.g.:

```python
colour_of_my_flag = request.form['flag_color']
```
..but **do not do that** here because being consistent about the names here is
the sensible thing to do.

You are explicitly seeing the data moving from one system (the HTTP request,
where it was named by the browser's `<form>`) to another (the Python app). You
can think of this as the data passing a boundary as it is handed from one
subsystem to another.


## Inspect the command to the database

If you've checked that `flag_color` contains the _right_ thing (i.e. you've
checked that it's working and your Python has extracted it from the form
correctly) you can add it to the database. This is fiddly so be careful with
the syntax:

This is the existing code. It's probably a good idea to break it over several
lines because it's already quite long (Python is very fussy about indentation at
the start of lines, but _inside_ a pair of `(` and `)` it is happy about you
breaking onto extra lines):

```python
cur.execute(
  "UPDATE buggies set qty_wheels=? WHERE id=?", 
  (qty_wheels, DEFAULT_BUGGY_ID)
)
```

The first `qty_wheels` there is **not** the variable name: it is the name of
the column in the database. _By no coincidence_ it's the same name as the
variable, but they are nonetheless different things.

This is another boundary between subsystems: Python is handing the data over
to the database (in this case, it's SQLite).

By using the _same name_ for the same datum on its way through the system you
are keeping things understandable. In more complex systems this is not possible
but in this case — because you have control over the HTML, Python, and
database, you can and should stick with this convention.

Note that the `UPDATE` command is [SQL](https://en.wikipedia.org/wiki/SQL).
It's _updating_ because the default editor comes with a database (if you
initialised it according to the instructions!) that contains a single buggy:
that database record is being updated each time the form is submitted.

## Modify command to the database

The `cur.execute()` call is from Python's 
[SQLite module](https://docs.python.org/3/library/sqlite3.html). The 
`cur.execute()` call has two parameters: 

1. the SQL statement you want to execute
2. a list of variables whose values you want that statement to use

In this case, each of the `?` in the statement will be replaced by the _value_
of the variable in the matching _position_ in the list. For this reason **it is
critical** that you put the _right number_ of variables in that list in the
_right order_.

Here's the new code: look carefully to see how it's been updated with
`flag_color`:

```python
cur.execute(
  "UPDATE buggies set qty_wheels=?, flag_color=? WHERE id=?", 
  (qty_wheels, flag_color, DEFAULT_BUGGY_ID)
)
```

Check that: three `?`s in the string containing the SQL statement, and three
items in the list in `()`.

The `DEFAULT_BUGGY_ID` is being used here so SQLite knows _which_ record in the
database to update. To start with there is only one (can you find in the
Python what value it has?) but later —
[3-MULTI]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-3-multi) — you might change
this.

## Review of what you just did

If you get this right, then when you send data from the browser the request
may have contained this form data:

```
qty_wheels=6
flag_color=blue
```

_then_ your Python should contain two variables with these names and values:

```python
qty_wheels = request.form['qty_wheels']  # => '6'
flag_color = request.form['flag_color']  # => 'blue'
```

And _then_ the SQL statement that `cur.execute()` constructs and executes will
be:

```SQL
UPDATE buggies set qty_wheels='6', flag_color='blue' WHERE id=1;
```

(If you are an experienced programmer, something to note: all the data coming
from the form is effectively a string... and SQLite is not quite as rigorous
as other SQL databases about what goes into its Integer columns.)

If that worked, you need to look into the database: we guided you with 
`flag_color` here because it was already in the database. But how did it get
in there?


---

* Prev: [add input tag to the form](add-input-to-form)
* Next: [what's in the database](database-structure)



