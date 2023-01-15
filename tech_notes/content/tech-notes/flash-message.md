Title: flash messages


# Flask's flash messages

---

It turns out it's very common to want to throw messages onto a web page based
on things that happen in your webserver (specifically, the controller) before
the template gets rendered. Flask has a mechanism for this called
_flash messages_.

## Sending one message

The buggy editor you started with did this in some templates (such as
`updated.html`) by passing a message as a _context_ argument in the
`render_template()` call, something like this:

```python
@app.route('/hello')
def hello():
   message = "Hello world!"
   return render_template('greeting.html', msg=message)
```

Then, in the template, you can display that message in the
`greeting.html` template with something like:

{% raw %}
```html
<p>{{ msg }}</p>
```
{% endraw %}

You probably added `class` and CSS styling to your paragraph there too, right?
Beautiful.


## Sending a list of messages

You might have found it's handy to send a _list_ of messages into a template,
instead of a single one (the original code had a single message in `msg`).

If you didn't realise this was possible, check the video for `3-MULTI`: the
Python passes a list called `buggies` into the template, which then does a
`for` loop over them.

```python
   messages = []
   messages.append("Hello world!")
   ...
   messages.append("I am a message")
   ...
   return render_template('greeting.html', list_of_msgs=messages)
```

If you did that, in your template you probably iterate over that list, using 
{% raw %}`{% for %}`{% endraw %}.


## Flashing messages

Flask has an in-built mechanism for _flashing messages up on a page_ that is
session-based.
See the [Flask documentation](https://flask.palletsprojects.com/en/1.1.x/patterns/flashing/).

For this to work, your app _must_ have a [secret key](secret-key).

```python
from flask import flash

@app.route('/hello')
def hello():
   flash("Hello world!")
   flash("I am a message")
   return render_template('greeting.html')
```

The powerful thing here is that Flask makes `get_flashed_messages()` available
inside templates (so the messages do _not_ need to be passed over as context
arguments).

For the buggy editor, you _probably_ only need this in the `base.html`
template, which every other template extends from. That means: if you put this
in `base.html` then any messages you have flashed will appear — once — at the
top of the web page of the response:

{% raw %}
```html
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul>
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
```
{% endraw %}

Maybe you should add a `class` attribute to the `<ul>` element and apply some
styling too?

When you declare a message with `flash()`, there is a second argument which 
allows you to specify a category too (by default, the category is `message`).
If you use this, you can change the loop to add the category as a class on
the `<li>` element.

{% raw %}
```python
    {% for category, message in messages %}
      <li class="{{ category }}">{{ message }}</li>
    {% endfor %}
```
{% endraw %}

Incidentally, this is how the messages are being displayed up on the
[buggy race server]({{ BUGGY_RACE_SERVER_URL }}).

### Extra detail: surviving redirects

There's a more subtle reason for using Flask's flash messages instead of
passing a message directly into the template. Because it's session-based, Flask
displays any flash messages it has at the first opportunity after they have
been set. Usually this is when it renders the template at the end of handling
this request. But sometimes the response is not a rendered template, but a 
redirect to another page. When this happens, you _can't_ pass any messages into
`render_template()` — but flash messages will still work.

This might not be happening in your buggy editor yet, but on more complex sites
it's common, for example, to catch an error and redirect the user to another
page on which the explanatory message appears.

---

* Prev: [Setting a secret key (sessions)](secret-key)


