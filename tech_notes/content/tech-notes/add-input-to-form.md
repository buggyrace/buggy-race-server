Title: 1-ADD add input to form


# Add one input to the form

* Task [1-ADD add more data to the form]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-add)

---

This example is going to add the **flag colour** to the buggy.

(Reminder: every racing buggy has to fly a pennant, or flag, and you can
to specify its colour using the editor you're building).

We recommend you start with this one because (as we'll see later), there's
already a column for it in your database.

You've [identified the correct template](identify-template) that you need to
edit, so this is editing the file `buggy-form.html`.

Here's the HTML for the form:

```html
<form action="/new" method="post">
  <label for="qty_wheels">Number of wheels:</label>
  <input type="text" name="qty_wheels" />
  <input type="submit" class="button">
</form>
```

When the user has filled in the form, pressing the `submit` button causes the
browser to send the data it has collected in the form as a request to the webserver. The request will use the HTTP method `POST` (because this time 
it's posting data to the server) and is targeting the route `/new`.

If you look at the Python code you can see it processes requests to `/new`
differently depending on whether the method was `GET` (just return the form)
or `POST` (accept the inputs from the form and save it in the database).

To add the colour of the flag, copy the pattern that's there for the number of
the wheels.

```html
<label for="flag_color">Colour of flag:</label>
<input type="text" name="flag_color" />
```

### Why the name you use is critically important

The important thing here is the `<input>` tag. That's the tag that tells your
browser to accept a string input. Critically, it needs a name so that when this
request gets to the server it knows what data it is. You _can_ call this input
anything you like... *but*... the smart thing to do is be consistent with the
name of the buggy data all the way through the stack. You're going to need to
refer to it in the form, in the Python code, in the database, and in the JSON
data that you're producing for the server.

That last one is the kicker: you *must* use the
[name specified by the server]({{ BUGGY_RACE_SERVER_URL }}/specs/)
when you submit your data there, so working backwards, it's smart to use the
_same name_ for the same item of data everywhere.

So: here it's `flag_color` (note the American spelling, because that's what
is being used at the far end (on the race server)).

### Other things about the form

You'll find that if you just add the HTML for the new input and its label, the
layout looks a bit rubbish. Why? What can you do to control that?

The `<label>` tag has a `for` attribute. What do you think that does? How can
you find out?
  
If you make a mistake and don't get the names right, the _form_ will almost
certainly still work up there on the browser, because at the moment it's not
doing anything other than collecting and sending the data. Your problems will
start when your Python can't make sense of what's coming in back at the
webserver.


---

* Prev: [identifying the template](identify-template)
* Next: [handle the POST request](handle-post)

