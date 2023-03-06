Title: secret key


# Setting a secret key (sessions)

* Task [4-USERS Add users (and sessions) so you know who is editing a buggy]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-4-users)

---

You haven't needed to think about this (unless you get to
[4-USERS]({{ BUGGY_RACE_SERVER_URL }}/project/tasks/#task-4-users)), but HTTP is a
_stateless_ protocol. Every request your server gets is treated like an
entirely new event, totally isolated from any other requests.

**There is no _state_ preserved between requests.**

So if you (using your browser) make a request to your buggy editor, get a
response, and make a another request, that second request is — within the
protocol, and from the point of view of your webserver — completely independent
of the first one.

You probably hadn't even noticed this until now because you are the only person
— using only one browser — sending the requests to your editor. (The situation
up on the [buggy race server]({{ BUGGY_RACE_SERVER_URL }}) is clearly
different, isn't it?).

However, even though HTTP might not support it, it clearly is possible to
implement statefulness on top of the protocol, because you know login _does_
work on websites. This tech note explains how.

## Flask supports sessions

Flask supports sessions, and you might find them useful in your project.
However, in order to use them, you **must** give your webserver a `SECRET_KEY`.

So: if you need to use sessions (and you might not... it depends what tasks you
implement) you need to set a secret key. Because your project is only in
development, and is really just an exercise, you don't _need_ to be strict
about how secret the secret part of it is (because you're only running on
`localhost`, not the web).

The correct way to give Flask a secret key is to
[set an environment variable](setting-env)
called `SECRET_KEY`.  Make it a string of bytes (basically: a string).

However if you're having difficulties with environment variables, _for this
project_ you can set the secret key directly by putting this in your `app.py`
near the top (the first line here is _already in your program_):

```python
app = Flask(__name__)
# Set the secret key to some random bytes
app.secret_key = b'_5#y2L!F4Q8z-9ec]/'
```

See this [in the Flask docs](https://flask.palletsprojects.com/en/1.1.x/quickstart/#sessions)

The rest of this page explains _why_ your webserver needs a secret key _if_
it's going to support sessions.


## Login example

Now, you know that websites — the [buggy race server]({{ BUGGY_RACE_SERVER_URL }})
for example — _do_ let you login. Requests you send after your correct username
and password combo are demonstrably handled differently from those you sent
before. Basically there is a _session_ at work. It's how you are able to login.
It's also how someone else is able to log in at the same time as you but the
webserver sends the two of you different things. The other user can't see your
buggy; you can't see theirs.

How does that work?  

It turns out there are a number of way to implement sessions but the most
common is by using [cookies](https://en.wikipedia.org/wiki/HTTP_cookie).

![cookies](assets/img/cookie.png) ![cookies](assets/img/cookie.png)
 ![cookies](assets/img/cookie.png)
  ![cookies](assets/img/cookie.png)

For this project you might not need to worry about cookies because if you need
sessions, Flask handles them for you (that is, although it implements sessions
using cookies so you typically don't need to manipulate them yourself).

But the concept is fairly simple:

* Whenever you visit a website, the webserver may add a cookie
  (it's really little more than a token) to the response it sends back.

* When your browser receives that response (maybe a webpage, or CSS, or 
  a graphic... any response), if a cookie came back with it too, your browser
  places it in its cookie jar.

* Then, _every time_ your browser is about to send a request to a website
  it reaches into its cookie jar first, asking the question:
  _has this website given me a cookie before?_

  * if it **has**, it takes the cookie out of the jar and sends it back to
    the server _along with the request_. That's where the cookie analogy
    breaks down: nobody is eating them... they are just sent out as an
    extra little gift with every request, and come back, piggybacking on the
    response.

If all browsers agree to behave in this way (and for now let's assume they do)
then it means the webserver can look for a cookie every time it gets a 
request. If there is one, it means this client (this browser... this _user_)
has been here before. If there isn't, they haven't. Simple right?

The extra kick is that the server can _write on that cookie_ and then send it
back with the response. In this way, the information written on the cookie
is how the webserver can tell the difference between your requests and mine
(because it writes different things on it). 

Unlike real cookies, web cookies don't get consumed: they are really just
tokens, being exchanged. The webserver generates them, and writes on them
(keeping track of the session, you see), and the client (your browser) stores
them and promises to always send them along with any requests it sends.

Cookies can expire (they have a time-to-live) or be deleted. That's one way
to end a session: when you logout, it destroys the cookie, so next time you
visit the website (without a cookie) you do so as a stranger and you won't
be logged in.

## Secret keys

This mechanism is very handy but it has a weakness: if I know what's written
on _your_ cookie I can simply write that on mine, and — because the protocol
is stateless — if I send that cookie to the webserver, it will give me a
response that really it should only be showing you.

This is clearly a security problem. In practice, it's a lot more complex than
this, but to understand the mechanism all you need to know is that, because of
this, sessions have a **secret key**.

The secret key is part of the cryptographic mechanism that means it's possible
for the server to write messages on cookies in such a way it can detect if they
have been tampered with. (If you're interested in how this _really_ works:
this is the maths and systems at the heart of the Information Security
specialism within Computer Science).


## Don't put secrets where other people can read them

The key needs to be secret — only known to the server — to prevent attackers
figuring out how to fake the secure tokens on the cookie. This is why it's 
commonly set in an environment variable: by definition, that's specific to
the environment where it's running (in this case, the webserver). 

That's why good practice would dictate that you _never_ put the value of your
secret key — just like any other password — in the program code itself.  If you
do that, then anyone who can read your program can read your key. Now it
may be that you know the program is _only_ available in that secure environment,
so that's OK. But that's quite a risky assumption, so be aware that _in general_
putting passwords or secrets in your source code is discouraged.

For this project it's OK for your project's secret key to be in the code,
partly because it's a development exercise, but mainly because you're the only
person running it, on your own machine.


---

* Next: [Flashing messages](flash-message)

