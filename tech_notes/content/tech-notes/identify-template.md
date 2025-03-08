Title: 1-ADD identifying template


# Identifying the template to edit

* Task [1-ADD add more data to the form]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add)

---

The first thing to do is to update the `<form>` tag in the HTML. Because the
editor is a small app it's relatively straightforward to find the relevant
template in the code — but you should also be able to work it out by inspecting
the URL you see in the browser:
  
![screenshot of form]({{ BUGGY_RACE_SERVER_URL }}/assets/img/identify-template.png)

That tells you the _route_ on the webserver to that page, that you got to by
clicking on a link on the preceding page. Your browser sent the request to
`GET` `/new`. That's enough information to identify the code that is invoked
for route `/new` with request method `GET`:
[specific line (27)]({{ BUGGY_EDITOR_REPO_URL }}/blob/master/app.py#L26) in `app.py`:

```python
return render_template("buggy-form.html")
```

That's how you know _which_ template you need to edit on the webserver to
change that form.

The `templates` directory is the default location for templates in Flask
applications.

That's how you know you need to edit `templates/buggy-form.html`.

---

* Next: [adding a new input to the form](add-input-to-form)

