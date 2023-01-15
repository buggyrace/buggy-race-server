Title: using localhost


# Using localhost (or 127.0.0.0)

* Task [0-RUN Get app running and view it in a browser]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-0-run)

---

When you run the buggy editor, you'll see its output includes this line:

    * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

If you go to [http://0.0.0.0:5000/](http://0.0.0.0:5000/) in your browser, you
_might_ see the buggy editor web page. But you might not — see the rest of this
tech note to understand why.

If `0.0.0.0` doesn't work for you, try [http://localhost:5000/](http://localhost:5000/) or
[http://127.0.0.0:5000/](http://127.0.0.0:5000/) instead.

## Explanation of IP lookups

Before we proceed, it's important to do a brief recap of what actually happens
when you type a URL into the address bar of your browser.

Let's suppose you want to go to everyone's favourite race server, so (for this
example) you type `{{ BUGGY_RACE_SERVER_URL }}` into the address bar. You could also
simply click on a link to the [race server]({{ BUGGY_RACE_SERVER_URL }}) — the
mechanism in this case is the same.

> That link works because your browser looks in the `href` (hyperlink
> reference) attribute of the anchor (`<a>`) tag in the HTML of this page,
> which looks like this:  
> `<a href="{{ BUGGY_RACE_SERVER_URL }}">race server</a>`  
> ...and effectively uses _that_ as the address just as if you had typed it
> into the address bar and hit ENTER.

What actually happens here?

Well, first of all the browser tries to fetch the page. It does this by
converting the web address — the text we've just entered — into an address that
it can understand, known as an IP address (the IP is the Internet Protocol). It
does this by carrying out a request for translation, known as a DNS request.
However, these records are typically stored elsewhere, such as on a server
operated by your internet service provider (ISP).

Now, this is all well and good: but what if the page is just for you, and you
don't want to host it on the internet? What if you're developing a website, but
you don't want to expose it to the world just yet?

> This of course is exactly the situation we've set up for your buggy editor
> project.

Thankfully, clever people have already thought of this, and have invented
special addresses called loopback addresses. These are addresses that the
browser intercepts and goes, "oh, I know what to do with these!" and instead
handles all of the routing locally. Two of these special addresses are:
`localhost` and `127.0.0.1` (in this case, these two are actually the same
thing).

So that's why when you run your buggy editor (which is a webserver: that's what
Flask is doing) you can visit it in your browser using `localhost` in the URL.


## What's the deal with 0.0.0.0?

So far, so good. So, what's the deal with 0.0.0.0?

Well, 0.0.0.0 is an even more special address. 0.0.0.0 is what's referred to as
a "non-routable meta address".

This is a mouthful, and for CS1999 you don't need to know what that means: all
you need to know is that this address can be used to say "accept messages from
all incoming local addresses".

That sounds powerful — because it is! But crucially, this happens at a lower
level than the browser. This means that the browser can get super-confused when
trying to route to it.

The solution here is to instead try to summon a different address: the best
solutions here are the other local addresses (for example, try localhost or 127.0.0.1) in your address bar instead.

### But _why_ is it telling you to connect to 0.0.0.0?

The very [last line of `app.py`](https://github.com/RHUL-CS-Projects/CS1999-buggy-race-editor/blob/main/app.py#L88) is doing this:

```python
    app.run(debug = True, host="0.0.0.0")
```

That's running the app and _explicitly_ setting the host address to `0.0.0.0`.
We put that in the code we've given you because it is forcing your buggy editor
to behave in the most consistent way regardless of which system _you_ are
running it on. In this context (running a Python webserver) pretty much all
operating systems that students might be using will map that onto localhost for
you; it's what repl.it expects too.

So your _Python_ program thinks it **is** running on 0.0.0.0. It is the
operating system it's running under that then connects _that_ to an address
your browser can find. On some systems that 0.0.0.0 might work, but as you've
seen, on some it won't.


## The port number (:5000) isn't part of this!

The IP address is used for _finding the right server on the internet_. The
number after the colon is the port number (in your case, 5000). This is
declaring what port number to use **once the server has been found** (it's like
an apartment number of a building in a postal address). So although you do need
the port number — try different port numbers and see what happens (it's safe!):
you _probably_ simply won't get a connection — it's not part of the IP
address.

The reason you don't normally see port numbers on URLs in daily life is because
most webservers (unlike your buggy editor) run on the default ports anyway. So
if you leave them out, it all works. Your buggy editor (Flask) does not run on
the default _just in case_ your computer is already running a webserver — if it
is, the buggy editor will fail to run with a message something like this:

    OSError: [Errno 48] Address already in use

If you see this error it's almost certainly because you've tried to run `app.py`
when you already have it running in another window.

