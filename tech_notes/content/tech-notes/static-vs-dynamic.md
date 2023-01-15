Title: static vs. dynamic


# Static vs. dynamic content

---

The basic idea behind HTTP is that your web browser sends a request to the
webserver and the webserver tries to send the thing it asked for back. That
thing might be an HTML page, a picture of a cat typing furiously at a keyboard,
or a style sheet (CSS).

## Static vs. dynamic

_Static_ resources are effectively files up on the webserver that are ready to
be sent straight back. The example in your editor project is the style sheet
`app.css` which is in the directory `static`. If a request with that name comes
in (`/static/app.css`), the webserver can respond immediately with that file's
contents.

This is very different from the HTML files in `templates`. They are _dynamic_
because — even though they might have the same resource name — their contents
might be different each and every time they are requested.

For example: what's on the **show buggy** page? The contents of that page are
different before and after you've edited your buggy. The resource has the same
name, but different content.

In practice this means:

* if `app.css` is requested, the webserver can just send it straight back.
  If you added any images, they were handled the same way: see the tech note on
  [static content](static-content).

* if a route (like `/new` or `/`) to dynamic content is requested, your Python
  needs to make the HTML before if can send it back: it renders the appropriate
  template by replacing the {% raw %}`{{ }}` and `{% %}`{% endraw %} bits in
  it with necessary stuff, before sending it back

Knowing that, you might notice that the "routes" (like `/new`) you've got in
your Python program are _only_ for the dynamic content. Your program _is_
handling the static content too, but you don't see it because anything coming
in with a name that starts with `static/` is automagically being handled for
you.


## Flask is doing this for you!

If you're wondering why you don't see explicit instructions to Python to do all
that then... good thinking! Because they must be there somewhere, right? Well,
they are: that's what the Flask library is doing for you. You don't need to put
all that in your own program, because you did 

```python
from flask import Flask, render_template, request, jsonify
```

Flask is really just a Python program that knows how to behave like a webserver
(specifically that's
[WSGI](https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface)), and your
program is using it. That's where things like `@routes` and `render_template()`
come from and — perhaps most importantly — why your program ends with
`app.run()`

In effect, `app.py` is where you define the "business logic" of what your
buggy editor does. Really that's the only thing that makes it behave differently
from every other webserver in the world. Once you've defined _that_, you
hand control back to Flask by telling it to **run** it.


---


* Next: [cache-busting the CSS](cache-busting-css)



