---
title: 1-ADD add with ALTER TABLE
---

{% include common.html %}

# Adding new columns to the data: ALTER TABLE

* Task [1-ADD add more data to the form]({{ site.baseurl }}/project/tasks/#task-1-add)

---

At the start of the project, if you're OK with 
[deleting the database and recreating it](adding-new-data-i),
then stick with that. But there is a better way.

SQL has a `ALTER TABLE` command that lets you modify the table without losing
the data it already contains.

Here's the
[SQLite documentation on ALTER TABLE](https://www.sqlite.org/lang_altertable.html)
(includes syntax diagram).

```python
con.execute("ALTER TABLE buggies ADD COLUMN power_type VARCHAR(20);")
```

Although you _could_ update `init_db.py` to modify the table in this way, that
seems wrong because you're no longer _initialising_ it.

Instead, you could make a new file (maybe something like `update_db.py`?) to
run. You'll need the same preamble to connect to the database that `init_db.py`
had.

But then you have a problem because maybe in the future you'll need to add even
more columns, and adding them to this file won't work because `ADD COLUMN` may
cause errors if you try to run it on a database table that already has that
column.

So it's not uncommon to end up with a file for each change... these changes are
called migrations. Often the migrations are timestamped or named with
incrementing numbers (because the order they are executed in a new installation
may be important). Read more about
[database (or schema) migrations](https://en.wikipedia.org/wiki/Schema_migration).

Python has a module called [Alembic](https://alembic.sqlalchemy.org/en/latest/)
that manages database migrations. That's probably overkill for this project
(but it is being used on the slightly more complex buggy race server).


---

* Prev: [add new data: CREATE TABLE](adding-new-data-i)


{% include footer.html %}
