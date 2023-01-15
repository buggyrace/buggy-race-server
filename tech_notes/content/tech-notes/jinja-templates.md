Title: templates in Flask


# Templates in Flask (where the HTML comes from)

* Task [1-TEMPLATE add a new template to the app]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-template)

---

When your webserver receives a request (from a browser) it nearly always needs
to send a web page back. That means returning HTML. Since that is really just
text, you can do that by returning a string that contains HTML (and in very
simple "Hello world" examples of Flask that is what you see). But the HTML
pages of your buggy editor are a little bit longer than "Hello world", so it's
more manageable to put the HTML for each page into its own file.

## HTML pages containing data = templates

But these aren't simply static web pages (HTML files) because they contain data
— for example, your racing buggy, or a message for the user — which may be
different for each request. So the pages are really _HTML templates_, which
Flask populates with the data you give it.

By default, Flask expects these templates to be in the `templates` directory.

They look like HTML files because most of their contents are indeed HTML. But
there's a bit more going on: you'll see {% raw %}`{{` and `}}`{% endraw %} for
placing _values_ (often these are variables) into the page, and {% raw %}`{%`
and `%}`{% endraw %} for some programming logic. That's how Flask knows where
(and how) to fill in the template with the values you give it.

The programming here _looks_ like Python (and is deliberately similar) but in
fact it's a templating language called Jinja:

* Flask's [documentation on Jinja templates](https://flask.palletsprojects.com/en/2.0.x/templating/)
* [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/templates/)


## Webservers using templates are very, very common

A huge number of the web pages you visit in your daily life on the web have
been prepared this way (curiously, the page you're reading right now isn't one
of them). It's very common that webpages are constructed from templates
populated with custom data.

If you want to understand a little more about this and its implications, see
the tech note about [static vs. dynamic content](static-vs-dynamic).

> There are different ways of adding custom content to web pages. Python Flask
> is doing it server-side but an increasingly popular alternative is to
> populate custom pages client-side — we're not looking at that mechanism in
> this project, but it's how JavaScript frameworks like Angular and React work.

## The templates extend `base.html`

If you look inside the templates in your buggy editor (that is, any of the
`.html` files inside the `templates` directory), you'll see they tend to have
this structure:

{% raw %}
```jinja
{% extends "base.html" %}

{% block content %}

  ...some HTML with curly brackets too...

{% endblock %}
```
{% endraw %}

That `extends` is telling Jinja (which is the "templating engine" that Flask
delegates this to) to base this on the contents of `base.html`. That's handy
because most of a webserver's pages actually have a lot of the same stuff in
them. In your case, it's how the same style information (CSS) is being applied
to all of your pages: that's all in one place — `templates/base.html` — which
all the other templates are using.

The `block` parts are specifying the start and end of the _content_ of this
page. Everything you put between those two is dropped into the _block content_
position in `base.html`.


## Render the template

You have to tell Flask to explicitly _render_ the template. That means you are
telling it not to simply grab the HTML and send it back, but to first replace or execute the things between the {%raw%}`{{ }}`s and `{% %}`s{%endraw%} in the
template.

Use the `render_template()` method — you need to tell it which template to use
(that's the first argument, and it's the template's filename), as well as the names and values of any data that need to be put inside it.

```python
return render_template('index.html', server_url=BUGGY_RACE_SERVER_URL)
```


When `render_template()` is done, it returns a string full of the populated
(rendered) HTML, which you need to `return` — Flask sends that back as the
response to the request from the browser that started this.

## Extra: Why can't you simply write Python in your templates?

Well, in theory you could (if Flask let you), but it's better programming
practice not to do that, so Flask uses Jinja.

Why is this?

The design principle behind this is known as the _separation of concerns_. In
this case, it's keeping your "business logic" separate from your "presentation
logic". In more sophisticated web frameworks you'll often see this implemented
as the Model-View-Controller (MVC) pattern.

In practice, this means you do all the data marshalling, preparation and
calculation in the request-handling part of the app (in your case, that's
`app.py`, and in the MVC pattern it's the "controller"). The output of that
process is then handed over as input to the presentation layer — so the only
decisions that should be made in the template are _how to display it_. That's
why templating languages are often quite limited compared to general
programming languages like Python: they're not supposed to be doing heavyweight
processing.

Here are two examples of why this is useful:

* **You can add entirely new presentation or formats**

  Firstly, for your buggy editor you're only concerned with HTML, but in bigger
  projects you might need to have different output formats. If your controller
  (your Python, or "controller") is cleanly separate from your view (your
  templates, or "view"), you could provide PDF or HTML output (depending on the
  request) — but clearly that shouldn't need you to change _how_ you're
  processing the data. Enforcing this separation means you can change almost
  _anything_ about the presentation without changing (and maybe breaking)
  the way the data is being affected.
  
* **Front-end and back-end coders can be different people**

  Secondly, it means the people working on the templates can be front-end
  designers and interface specialists who don't need to know _how_ the data
  processing works. In fact, they don't even need to know the programming
  language it is written in (in this case Python... but maybe in the future that
  could change, right?).


---

* Next: [routes in Flask](routes-in-flask)

