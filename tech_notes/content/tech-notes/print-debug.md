Title: printing debug


# Printing debug

---

This tech note is a simple tip for debugging your Flask app.

If you are trying to figure out what is going on in your program, *especially
when it isn't working*, put some `print()` statements in there.


## Use print()

Say you're not sure if you've set `qty_wheels` correctly. Don't guess!
Print it out:

```python
print("FIXME: qty_wheels is ", qty_wheels)
```

Sometimes you just need to know Python really _is_ getting to the bit of the
program you think it is:

```python
print("---------------->>> FIXME hello! I am here!")
```

...and look out for when your webserver next gets a request. Maybe `hello` does
or it does not appear: either way you now know something is or is not happening.

This inside information is especially helpful when you are working on a
webserver where (if you look at the browser) you only see the start (click!)
and end (page or error) of the process.

## Where does this show up?

In the terminal where you ran your program!

You're already seeing flask's `print`s coming out when your webserver logs the
record of its response.

Test it by putting this in your `home()` procedure:

```python
@app.route('/')
def home():
    print("FIXME hello world!")
    return render_template('index.html', server_url=BUGGY_RACE_SERVER_URL)
```

...and hit the home page in your browser.

See "hello world!" in your terminal output?

 
## When you've got things working, take them out

When you're done carefully delete these `print()` lines.

Be careful because you don't want to delete the _actual program code_
you were debugging!

If you're not sure if you've finished, comment them out so you can quickly
switch them on and off again. 

```python
    # print("FIXME hello world!")
```

While you are debugging, use any mechanism you can to _get more information_. 


## Why "FIXME"?

You can put anything you like in your debugging print statements.

That `---------------->>>` makes it easy to spot. No other reason.

These print statements are to help you debug so _obviously_ they shouldn't end
up in your final program... you take them out when you've figured out what you
were trying to debug.

`FIXME` is a special word some programmers use because it's a word that you'll
never normally use. So if you have the discipline of always using the word in
your debug statements, later you can search your program for the word "FIXME"
to check you haven't left any debug statements in your work.

In fact, some programmers add a
[commit hook](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
to their Git so it will refuse to let them commit any code that has the word
`FIXME` in it.


### This page is special...

...because it really does contain the word "FIXME" :-/


