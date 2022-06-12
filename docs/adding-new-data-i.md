---
title: 1-ADD add new columns
---

{% include common.html %}

# Adding new columns to the data: CREATE TABLE

* Task [1-ADD add more data to the form]({{ site.baseurl }}/project/tasks/#task-1-add)

---

The simplest way to add new data to the database is to add it to the
`init_db.py` script where the table is created.

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

See the pattern there? The order of the columns isn't important, so it's
probably easiest to add next columns to the end of the list. Remember to add
a comma to the end of the previous one you're joining on to.

For example to add `power_type`, add:

```python
    power_type VARCHAR(20)
```

You can add more than one column at the same time, of course. It's up to you.
Similarly, you don't have to use a limit of 20 characters.

## The catch with `init_db.py`

Changing the code in `init_db.py` won't make any difference until you run it.
And even then it's got `IF NOT EXISTS` in there which means it won't have any
effect because it's already been run. (That's in there to prevent you
accidentally overwriting the database when you run the script).

The solution is to _delete the database_ and _then_ run it. (Unix/Mac use `rm`
(remove), Windows CMD/Powershell use `del`):

```
rm database.db
python3 init_db.py
```

Obviously this has the side-effect of destroying all the data in the database.

However, while you are developing your editor, it might be common that there's
no data in there you want to save, because the single buggy record is pretty
basic.



---

* Prev: [know what's in the database](database-structure)
* Next: [add new data: ALTER TABLE](adding-new-data-ii)


{% include footer.html %}
