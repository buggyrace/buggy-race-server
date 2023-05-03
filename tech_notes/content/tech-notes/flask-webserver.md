Title: Flask as a webserver

# How Flask works as a webserver

Make sure you've seen the description of [how a webserver works](webserver),
because this page follows from that one. In that example, the webserver's
response to each request is to send back the contents of one of the files
it has in its "server root" directory. That's the simplest way to understand
how webservers work (and it's useful: it is how webservers handle
[static content](static-content), which is a big part of the web).

In that example, this is the process that the webserver follows each time
a request arrives:

1. determine what _resource_ the request is for (by looking at the route or
   path of the URL)
2. find the file corresponding to that route
3. read it
4. send its contents back (as the body of the response)

Flask replaces that with a very similar process. But instead of finding a _file_,
it finds the _method_ that matches what the request is for (again, by looking at
the route, or path, that is in the URL). It runs that method, which ultimately
produces a string (that is, text), and sends that text back. For an HTML page,
that text is a description of the contents of the page.

> At this point, it's no longer accurate to say that the request is for a
> file — which is why the things being requested are called _resources_.
> That's what the R in URL stands for: it's a **Universal Resource Locator**
> (a descriptor that identifies how to find a specific resource, anywhere
> on the world-wide web).

In the simplest case, the text really could just be "Hello world":

```python
@app.route("/")
def welcome():
    return "Hello world!"
```

The `@app.route()` line is a
[Python decorator](https://en.wikipedia.org/wiki/Python_syntax_and_semantics#Decorators)
telling Flask to run this method if the incoming request's route matches `/`.

The route `/` matches _no path_, so `http://localhost:5000/` (or 
`http://localhost:5000`) would respond with "Hello world!" (and a
status of
[`200` — _success_](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200)),
but  `http://localhost:5000/something` would not, because there's no
route for `something`. (In that case, Flask's would send a response with the status code 
[`404` — _not found_](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404)).


Typically, it's more complicated than that, and the method involves some form of
processing. It might do a calculation and send the result back, or read the data
from the database. Very offten that result must be an HTML page, so often the
process consists of gathering or caluclating information, getting a template HTML
file, and putting the results into that template. Taking the template and
populating it with the information to produce a string is called _rendering_
the template.

The Python library Flask manages this process. It listens to the port, matches
incoming requests with the right methods (using `@route`), and — where necessary
— renders HTML templates.


## Not just getting, but also posting

In the original example, the process was effectively just a _file server_.
But Python is a general programming language, so you can perform arbitrarily
complex processes to determine what response should be sent back.

Those processes might actually _do_ things, before sending the response
back. That is, a request need not just be to <code>GET</code> something.
For example, in the buggy editor you can `POST` data for it to
save in the database (maybe the _number of wheels_). The Flask app
does that task, and the response it sends back depends on whether or
not it succeeded.

> In fact there are
>[other methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
> (sometimes called "verbs") besides `GET` and `POST` that you can use to
> make web requests.

## What are the limits?

Although it's true you can do any aribitraty complex thing in response to
the request, if you take too long, the client (that is, the browser that
issued the request) may _time out_ and give up waiting for a response.

Busy webservers can also have the problem of dealing with hundreds or
even thousands of requests coming in every second — this can have
similarly bad consequences if the responses cannot be handled promptly.

The are many techniques for dealing with these things — one you have
probably encountered already is cacheing (see the tech note about how to
[bust the CSS cache](cache-busing-css)). But this is also an example of
why just being able to write source code is not enough. Your buggy editor
is probably running a replatively simple task for a single, infrequent
user, so it's actually a forgiving environment in which to do your
web development. But professional web developers working on apps that
need to do a lot of calculation or handle high volumes of traffic always
need not only to write source code, but to understand how to write
programs that are efficient.

<script src="{static}/assets/js/ksd.js"></script>

