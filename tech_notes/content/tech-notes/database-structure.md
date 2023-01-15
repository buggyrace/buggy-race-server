Title: 1-ADD database structure


# know what's in the database

* Task [1-ADD add more data to the form]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add)

---

When the buggy editor is correctly initialised, the database contains one
record: that's the buggy which your are updating when you submit the "Make
buggy" form.

But it's not a mystery how it got there. After you cloned your editor, you ran:

```
python3 init_db.py
```

That populated the database that the webserver needed.

If you didn't run it, you'll get a `error in update operation` error message
when you try to make a buggy.

If you look inside the `init_db.py` you see some Python mixed in with some
[SQL](https://en.wikipedia.org/wiki/SQL). It doesn't matter if you've not
really learned SQL yet, because the code is already there for you, and in the
next tech note we show you the edit you need to make.

But the key thing is that in the database you can see the columns that are
defined:

```python
con.execute("""

  CREATE TABLE IF NOT EXISTS buggies (
    id                    INTEGER PRIMARY KEY,
    qty_wheels            INTEGER DEFAULT 4,
    flag_color            VARCHAR(20),
    flag_color_secondary  VARCHAR(20),
    flag_pattern          VARCHAR(20)
  )
  
""")
```

Relational databases (which is what this is) are divided into _tables_ of data.
Your editor has only one, called `buggies`, because that's the only kind of
thing you're storing at the moment. (Later, in
[4-USERS]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-4-users) you might add
another table called `users`).

You should recognise the names in the declaration that follows: those are
_columns_, each one for a different setting for your buggy, using the
[same names as the spec]({{ BUGGY_RACE_SERVER_URL }}/specs/).

You can see that `flag_color` is already there (that's why we suggested you
go with that one first when doing 
[1-ADD]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add)).

You'll notice that all the items are not yet there: you can add more (we'll
describe that in next tech note [updating init_db.py](updating_init_db)). But
the key thing is to see what _is_ there.

Each column has a name, a type, and (optionally) a default value.

As explained earlier, it's a _very good idea_ to use the same _name_ for the
same item of data throughout the stack: here it's the database column name, but
you've also got the variable name in Python, the form name in the HTML, and the
name in the JSON data up on the race server.

The _type_ of the column here is either `INTEGER` or `VARCHAR(20)`.

* `INTEGER` columns are good for numbers of course (note though that SQLite,
  which is the database your editor is using, will let you put strings in there
  too: that might be why you need to do
  [1-VALID]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-valid) to stop `banana`
  going into `qty_wheels`).

* `VARCHAR(20)` columns are for storing text (it means "variable length
  character string", with a length up to the stated limit). That's _probably_
  long enough to store any of the values your buggy needs¹.

The `id` is used to identify different buggies. To start with, you only have
one, which you keep updating. Later, you might add more with
[3-MULTI]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-3-multi).

## Where is the database?

More sophisticated databases run as servers, but SQLite is much simpler, which
is why it's great for your editor. For this project, it puts everything in a
file called `database.db`.

When you run `init_db.py` it will create that file if it doesn't already
exist, and thereby create the database.

### Why can't you look inside `database.db`?

It's stored as a binary file, which means it's not arranged as text characters
that you can simply read. If you try to read it in a text editor, for example,
you'll see it doesn't make any sense.

One way to investigate the contents of and SQLite database is by
installing and running [SQLite](https://sqlite.org/index.html) itself. But you
can also access it through the `sqlite` Python module (which ships as part of
standard Python3 now)... which is how your buggy editor is doing it.

### Why don't all the columns have default values?

They could do! You could add them if you think you know what they are.
But _maybe_ the database is the wrong place to be enforcing that. What
happens if they change? Is that likely?

<br><br>

¹ What's the longest
[CSS colour value](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value) 
that `flag_color` might contain?



---

* Prev: [handle the POST request](handle-post)
* Next: [add new data: CREATE TABLE](adding-new-data-i)

