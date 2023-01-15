Title: 1-STYLE cache-busting CSS


# Cache-busting the CSS

* Task [1-STYLE style your editor just how you like it]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-1-style)

---

If you're changing the way your editor looks by changing the CSS file (which
is the right way to do it!) you might bump into a problem with caching.

You edit the CSS file (e.g., to make the **Make Buggy** `submit` button blue
instead of green), save it in your editor, refresh the page... and nothing
changes. Maybe when you change the HTML in the template, and refresh the
browser the new HTML appears... but changes to the CSS aren't coming through.

What's going on? **Caching!**

Before you can understand this, you need to know the difference between
[static and dynamic content](static-vs-dynamic).

## Caching helps in production

[Caching is a complex subject](https://en.wikipedia.org/wiki/Cache_%28computing%29)
but the idea is simple. Also, it turns up in a lot of places in computing.

Later, as a software developer, it's going to trip you up in all sorts of
annoying ways. But for now we're just looking at caching in your browser.

Before your browser sends a request to your webserver, it checks to see if it
already has the thing it's asking for. That is, if the server has _already_
sent this thing maybe we can reuse that and don't need to bother with a request.

That works because when the webserver sends content back, it includes a
"time-to-live" lifespan that indicates how long this resource is good for
reuse. If content has such a lifespan, your browser saves it in its **cache**.
The next time it needs it, instead of sending a request, it can use that cached
copy. Simple, right? This means — especially for websites with a lot of static
content, like pictures or big stylesheets or JavaScript — the page loads much
faster the second time.

In most situations static content is not going to change between requests, so
the server might put a time-to-live of an hour, or a week or even a year.

## Caching doesn't help in development

That's why this is a pain when you are developing your website: now this
mechanism is working against you. You browser thinks it's helping by _not_
refreshing the stuff that Flask has just told it to reuse.

So this tech note, as well as explaining why you're getting this problem, shows
you a number of ways to try to deal with it.


## Static content is cached more aggressively

In a production environment, you _want_ everything to be cached as much as
possible because it results in fewer requests being sent. This means pages load
faster (there's a whole bunch of request-response round trips that the page
doesn't have to wait for any more) and the server is less busy, because it gets
fewer requests to handle.

But by definition, dynamic content often can't be cached: despite the resource
having the same name (e.g., `/buggy`) the _response_ might be different every
time (because your buggy changes, right? — the app is an editor!).

Flask understands this, so it will set a high time-to-live on static content,
but a zero on dynamic content. Zero time-to-live is the server telling the
browser: here's what you asked for, and you can display it but don't save it,
because I _know_ I might have something different for you next time you ask.

Notice how the webserver, not the browser, is making decisions about the nature
of the thing it's sending back. That's because the browser usually doesn't
really know anything about the resource when it makes the request. Might be
static. Might be dynamic. Can't know. OK, so in your buggy editor all the
static content happens to start with `/static` in its path... but that's just a
convenience for you for now, and it doesn't _need_ to be like that.

And this is why you can have everything working in your buggy editor and reloading
nicely in your browser except the CSS, which is sticking in your cache.


## Watching webserver responses to understand caching

You can see this happening, of course.

If the browser makes the decision to use content from the cache it won't send a
request. It doesn't need to.

You can see this by refreshing your editor home page, and looking in the
webserver's output. You'll see something like this appear:

```
127.0.0.1 - - [timestamp] "GET / HTTP/1.1" 200
```

That's the webserver reporting that your browser asked for the thing called
`/` (which is to say: no named resource, so get whatever is at the "root"...
i.e., the home page).

If you don't see anything after that, then **there was no other request**. You
know your browser has used CSS (because the page looks pretty) but it _hasn't
sent a request for it_ ...so it must be using the cached copy.

However, if you also see this immediately after:

```
127.0.0.1 - - [timestamp] "GET /static/app.css HTTP/1.1" 200
```

...that's the browser asking for the CSS stylesheet too, and the webserver
sending it back
([200 means Success](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200):
the request was handled without problem and the response sent back OK). So you
know it wasn't cached. (But remember that as soon as the browser got that
response, maybe it cached it... depends on what the time-to-live your webserver
sent it back with).

However you might see:

```
127.0.0.1 - - [timestamp] "GET /static/app.css HTTP/1.1" 304
```

...that's the browser asking for the CSS stylesheet too, and the webserver
sending back the response "No! Use the one you've got".
([304 means Not Modified](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/304):
the request was for a thing that the browser already has, and the server is
confirming it hasn't changed since the browser last asked for it... so the
browser can use the cached version).

That last one is what happens after the time-to-live has expired _or_ if you
force the browser to make a request anyway. That might happen if you 
do a hard refresh (shift-Crl-F5 maybe)
or _explicitly_ make a request for it by hitting 
[http://localhost:5000/static/app.css](http://localhost:5000/static/app.css).


## How to beat the cache

Okaaaay.... so that's why this problem exists: most of the time (when you are
browsing) caching is making your life better because static content doesn't
change.

But when you are developing you are in the perverse situation where static
content is not static: you are frequently changing it.

Here are some of the approaches to "busting the cache".

The last one (5) works all the time (so it's probably a good idea to do it).
But you must appreciate that is unacceptable in a production environment...
precisely _because it works all the time!_ That's OK in your buggy editor
because actually it's only ever you who is using it, on your localhost, but
don't do this when you are programming a commercial webserver.


## Remedy 1: clear your brower's cache

The simple way to fix this is to delete your browser cache. That will _always_
work because if the file isn't there, your browser can't display it, so it
_must_ make a new request.

The catch is it's a pain to do that _every time_ you change the CSS file to see
what it looks like. And you will probably have to keep doing it if the CSS keeps
getting cached... every single time you load it.

## Remedy 2: disable you browser's cache

It may be possible (depending on your browser, and if you can find the developer
tools on it) to instruct your browser to simply _not use the cache_.

The good thing about this is it solves all your caching problems.

The bad thing is you'll forget and wonder why the internet is always so slow.
Hmm.

## Remedy 3: don't run in production environment

Flask sets the time-to-live on static content differently if it thinks it's
running in a real, production environment. If this happens even once, your
CSS will be in the browser, cached (see remedy 1). Because you're basically
always changing things on the webserver in this project, it's probably not
helpful to ever run in production.

That's why we recommend you set the environment variable `FLASK_ENV` to
`development`. You have to do this differently on different operating systems
(see tech note on [setting Flask environment variables](setting-env)) but
something like:

* Windows powershell: `set FLASK_ENV=development` ...and then run your program

* Unix/Mac/Git Bash: `FLASK_ENV=development python3 app.py` (maybe `python3`
  should be `py` on your machine)

How well this solves the problem may depend on your browser settings too. But
certainly running in production mode _does not help_.  Remember, if you've
done it even once then your browser has probably cached the CSS, which might
trip you up.

## Remedy 4: tell flask to add zero time-to-live on the CSS

This is a good solution but if that's not already happening for you (despite
you running in development environment), for the scope of this project it's
probably best to go onto...

## Remedy 5: add a cache-buster to the resource name

This is the power-play. Caching works on the assumption the webserver and 
browser are identifying the resource by its name. So the trick here is to get
your browser to use a different name from last time when it makes its request.

The reason you can do this easily in the buggy editor is because you know the
HTML you're loading is dynamic: your Python is _always_ processing the template
before it sends it back. So if you edit `templates/base.html` and change the URL
of the CSS style sheet from this:

```python
<link href="static/app.css" ...>
```

...to this:

{% raw %}
```python
<link href="static/app.css?{{ range(1, 9999) | random }}" ...>
```
{% endraw %}

...you'll be adding a `?` and a random number (between 1 and 9999) to the name
of the resource your browser will ask for _every time_ a new HTML page is
loaded. So instead of requesting `/static/app.css`, your browser will ask for
`/static/app.css?4365` or something. It so happens that your Python will
ignore everything after the `?` in the URL for static content... but the
browser doesn't know that.

This is working on the server-side because if you look at all your templates
you'll see:

{% raw %}
```python
{% extends "base.html" %}
```
{% endraw %}

...in there. That's how all the pages are getting the same `<html>` and CSS:
they're really templates-in-tempates.

## Cache-busting in the real world

This "cache busting" technique is actually very common in production sites, but
not on _every_ request like you're doing it. (That would defeat the whole point
of caching). Instead, it's common for the cache-buster number to change every
time new or updated static content is deployed on production. So you might
change your CSS file twenty times on your development site while you are
fiddling with the colour. But once you have decided, you publish that new CSS
on the production site. At that moment, you change the cache-buster up there
just once. That bypasses all the caches of all the browsers out there in the
world that had already cached the old one, and instead they load (and cache)
the new one.

Here's the stylesheet URL from the
[college's website](https://www.royalholloway.ac.uk):

```html
<link href="/bundles/main-css?v=shCmkLK_cbodQXvV1YDOortkWaTOHK_uh659zf9ZeJI1"
  rel="stylesheet">
```
See the cache-buster there? That number/hash will be the same _until_ the next
time a developer or designer modifies the stylesheet, and then it will change.
On the college site, do _View page source_ and see if you can find
that CSS link (it will be somewhere in the `<head>` element near the top).
Can you see if the cache-buster has changed since this tech note was published?

Why is this different from what you're doing by adding `random` to `base.html`?
Because you're using a new cache-buster number *for every request*, which means
it's forcing a new request even when file has **not** changed. The real-world
use of this technique is *for every new deployment*, which only happens each
time the file is changed.

...or look at the header of this page (view source now!). Can you see the
cache-buster? The tech notes you're reading are
[100% static](static-content#can-you-have-a-website-that-is-totally-static).

<br><br><br>
More information for looking deeper:

* The negotiation over caching happens in the
  [request and response headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers).

* You can see the browser telling the webserver if it already has a resource
  when it makes a request by opening the dev/inspector tools in your browser
  and looking in the "network" section. See if you can find the Request's
  **headers**: specifically it's the `If-Modified-Since` header. The server can
  either send back `200 Success` (together with the content requested) or else
  `304 Not Modified` (so reuse the one you've got).

* The description above uses "time-to-live" but actually it's not really called
  that: see [cache control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
  for the real details (basically it's a more complex variation of `max-age`
  and `expires` and other directives too).

* See Flask's documentation on programmatically getting the time-to-live setting:
  [get_send_file_max_age](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.get_send_file_max_age).
  
* Caching on the web is more complicated than this because the cache in your
  browser is just one of the places this is happening: that's a _forward cache_.
  To stop busy sites being overwhelmed by requests, there are _reverse caches_
  and _CDNs_ too. Luckily for the buggy editor project, there are no reverse
  caches between your browser and localhost, so the browser cache is probably
  the only one you'll have to worry about.

---


* Prev: [static vs. dynamic](static-vs-dynamic)


