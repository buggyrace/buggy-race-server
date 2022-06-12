---
title: routes in Flask
---


{% include common.html %}

# Routes in Flask (how it picks the right template)

* Task [1-TEMPLATE add a new template to the app]({{ site.baseurl }}/project/tasks/#task-1-template)

---

Your webserver effectively has three jobs:

1. listen for incoming requests (from the browser)
2. do the processing for that request (maybe manipulating some buggy data)
3. find the right [HTML template](jinja-templates) to render (and send back)

Flask takes care of 1. for you. When you tell Python to run `app.py`, it's
listening on [localhost:5000](http://localhost:5000/) (there's a
[tech note about localhost](localhost)) and leaps into action as soon as a
request comes in.

Step 2. is done by Flask finding the right bit of code in `app.py` to run for
the incoming request. That _finding the right bit of code_ is where routes
are used.

Finally, that bit of code (a function in Python) handles 3. too, which in most
cases means the last thing it does usually something like this:

```python
    return render_template("name-of-template.html", name_of_thing=some_variable)
```

## Finding the right bit of code to run

Your buggy editor webserver is implemented as a Python program in `app.py`.

It's broken down into separate functions — chunks of code, which happen to be
named. Flask decides which one to run by looking at the incoming request and
asking two questions:

* what thing is this request for?
  * it might be `/info` or `/new` or maybe just `/` (nothing)
  * this is the _route_ and Flask extracts it from the request's URL
* how does it want to do it?
  * it's usually `GET` (meaning: "get me this thing")...
  * ...but you'll also see `POST` (meaning "I'm posting this data to you to use")
  * this is called the _method_

So Flask takes the request and executes the first function it can find that
matches the route and method. That's it.

## What that looks like in `app.py`

Flask uses Python decorators to indicate which route(s) and, optionally,
method(s) a specific function applies to.

It starts at the top of the program and works down: the first match it finds
will be the one it runs. (So the order of things in `app.py` matters, although
presumably you'd only have one function for any given request anyway).

### A minimal example: `GET /`

For example, the first `@app.route`-decorated function in `app.py` is this:

```python
@app.route('/')
def home():
    return render_template('index.html', server_url=BUGGY_RACE_SERVER_URL)
```

This tells Flask to run the `home()` function if the route of the request is
`/` (which means: root, or _no named route_):

* the function is called `home()` but at this point the name doesn't really
  matter except to make it clear what it's for — in this case, it's your
  buggy editor's home page

* the only thing this function is doing is returning the value produced by
  called `render_template()`

* the template it renders is called `index.html`

* it's also providing a value (`BUGGY_RACE_SERVER_URL` — which is a constant
  that you can see being declared earlier in the program) with the name
  `server_url`: that's so Jinja (which handles filling in the templates) knows
  what value to put in the place in the template for `server_url`

There's nothing there about what method this needs to be, so Flask will run
this in response to any request for the route `/` regardless of what method
it was sent with.

That's why if you run your buggy editor and hit [`localhost:5000`](http://localhost:5000/),
you've made a `GET` request with no route (just `/`) — and you get back the
home page that's effectively described in `/templates/index.html`.

> If you leave the `/` off your URL, and provide no route name, it's
> implicitly added to the request.


### A slightly more complex example: `GET /new`

If you click on the "Make buggy" button, the URL your browser will try to load
is [`localhost:5000/new`](http://localhost:5000/new).

Now the incoming request is:

* route is `/new`
* method is `GET` (again)

This time the route doesn't match `/` so `home()` isn't picked. Instead Flask
works its way through `app.py` looking for a match. It finds this:

```python
@app.route('/new', methods = ['POST', 'GET'])
def create_buggy():
```

You can see the `/new` here, and this time there is an explicit list of methods:
`GET` is in there, so this is a match. As a result, Flask will execute
`create_buggy()` to generate its response to a request to `GET` `/new` (which
in this case gets the form for creating a buggy).


## Why "route" and not "URL"?

You might wonder why Flask is only looking at the route, and not the whole
URL (that is, the subdomain and domain).

The _route_ is effectively the path part of the URL. That is, if your webserver
were a static fileserver, then it's just like asking for files from a
directory. In fact, that's fundamentally how your buggy editor _does_ serve the
[static resources](static-content) (images and CSS files).

The answer — in the case of your buggy editor running on localhost — is
straightforward: everything up to the route in the URL already _has_ been used:
that's how the request has ended up being handed to `app.py` and not some other
program.

However, it _is_ entirely feasible for the same process to accept requests from
different domains and subdomains, in which case testing those components of the
URL would make sense too. You don't need to do that for your buggy editor
because by design it's the only service running on this webserver.


---

* Prev: [templates in Flask](jinja-templates)


{% include footer.html %}
