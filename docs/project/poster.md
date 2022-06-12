---
redirect_from: "/poster/"
---

{% include common.html %}

---

* CS1999: Foundation Year Computer Science project:
  [submission information]({{ site.baseurl }}/project)

* [step-by-step workflow]({{ site.baseurl }}/workflow)

---

# CS1999 submission: your poster

## About the "poster"

There are two parts of your project submission:

* your Racing Buggy Editor web application
* a "poster" summarising your work

Because you have developed a webserver, for **Computer Science** CS1999
your "poster" is — of course — a page on your webserver at

* [http://localhost:5000/poster](ttp://localhost:5000/poster)


## What is on your poster?

There are two parts: the top and the bottom (of the single web page):

* top: "sell" the features of your editor
* bottom: notes on each task you attempted

## What is on the top of your poster? 

You've made a working (up to a point) buggy editor! Tell someone who lands
on this page what's great about it! What does it offer? What can you do with
it? What features does it have? Use CSS, use images if you want, but think
about the information you're presenting too.

Here are examples of webpages that do this for _their_ editors: this is only
for inspiration, you can make it your own!

* [VSCode](https://code.visualstudio.com/) our main code editor for this module 
* [Notepad++](https://notepad-plus-plus.org) a Windows text editor
* [TextMate](https://macromates.com) the text editor you've seen me use in the
  videos
* [Atom](https://atom.io) The Atom text editor

Obviously some of those have the power of a team of pro graphic designers
behind them so it's OK if yours isn't a complete festival for the eyes... but
you know enough about HTML now to know how to organise headings and paragraphs
or maybe bullet lists or... well, see how you get on with HTML and style...

...but don't forget this is about conveying the _features_ your editor has.

##  What is on the bottom of your poster?

Underneath that we want to see a list of the tasks your attempted with a
couple of sentences on each: what you did and anything you did and didn't
do. This is where we can give you credit for your _understanding_ even if
you didn't manage to get all of the task working.


## How to set it up

As you'll know by the time you set this up, there is more than one way to do
this, but you are *strongly recommended* to add your poster like this:

In `app.py` add another route (drop it in with your other routes, which means
somewhere _before_ `app.run()` is called):

```python
@app.route('/poster')
def poster():
   return render_template('poster.html')
```

Incidentally this makes sense to you because you know how Flask webservers work
now. How cool is that? Well done!


And in `templates/poster.html` add this: (maybe copy-and-paste it?)
(we've written the first one — `0-GET` for you as an example — of course
you can edit it!)

{% raw %}
```html
{% extends "base.html" %}
{% block content %}

<style>
  .cs1999-tasks {
    border-top: 1px solid black;
    margin-top: 4em;
  }
  .cs1999-tasks .task {
    margin: 1em;
    padding: 1em;
    border: 1px solid black;
  }
  .cs1999-tasks .task h2 {
    border-bottom: 3px solid gray;
  }
</style>

<!-- see tech note about the poster:  
      https://rhul-cs-projects.github.io/CS1999-buggy-race-server/                -->
<!--                                                                              -->
<!-- anything you want here: make it beautiful! make it appealing! make it clear! -->
<!-- you can drop images into static/assets if you want... and access them        -->
<!-- here with <img src="/static/image-filename.png" alt="diagram" />             -->
<!--                                                                              -->
<!-- Of course you can edit static/app.css too if you want. It's your webserver,  -->
<!--                                                                              -->
<!-- Maybe... delete all these comments too :-)                                   -->


<!-- below this point keep this section tag and paste in a <div> for every        -->
<!-- task you attempted.                                                          -->

<section class="cs1999-tasks">

  <div class="task">
    <h2>0-GET</h2>
    <p>
      I forked the repo on GitHub and then used <code>git clone</code> to make a local copy.
    </p>
    <p>
      Once the repo was on my own machine I was able to commit changes to version control
      as I went along, and I pushed back up to my GitHub repo at the end of each day.
      I followed GitHub's instructions and set up a SSH key so I didn't need to enter
      username and password every time I pushed.
    </p>
  </div>


<!-- this closes the section: keep it in! -->
</section>

{% endblock %}
```
{% endraw %}

## Add a note for every task you attempted

We'll be looking at the code to see _what_ you did, but in the notes just
drop a short paragraph saying _what you did_. And what was tricky or anything
you learned.

We're looking for opportunities to give you credit for having _understood_
what you were doing. That's why it's OK if you didn't do a task completely:
tell us why.

For example, for 1-VALID the different _types_ of data are not equally easy
to validate. "I did not validate the `xyz` field in the same way as
`qty_wheels` because...". You need to show us you understood what you did
(and learned from it) so sometimes that includes explaining the bits you didn't
do, and why. Doing is better than not doing, obviously: but if you couldn't
do a complete task you can still get some credit for it if it's clear you dived
into it.

### Keep your notes short!

Just a couple of sentences on what you did is fine (it _might_ just be stating
the task's solution if you think it was straightforward).


## Helpful HTML to copy-and-paste

Here is HTML for you to copy-and-paste: for each task you attempted, take
this and add it to your poster (in the `cs1999-tasks` `section`).
Be kind to your marker and put them in the right order too please ;-)

**REMEMBER** nobody was expected to do them all! If you did all of
 Phase 3 task you've done well — if you got onto Phase 4 or beyond you've done
 very well.

<!-- POSTER-TASK-HTML-START -->

```html
<div class="task">
  <h2>0-GET Get the source code</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>0-RUN Get app running and view it in a browser</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>0-CHANGE Make a change to a template and see it appear</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>1-TEMPLATE Add a new template to the app</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>1-ADD Add more data to the form</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>1-VALID Add basic data validation</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>1-STYLE Style your editor just how you like it</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>2-EDIT Edit the record by loading its current values into the form</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>2-FORM Make the form better</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>2-COST Calculate and save the game cost of the buggy</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>2-RULES Add validation according to the game rules</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-ENV Switch between dev and production environments</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-AUTOFILL Add auto-fill to the edit forms</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-MULTI Allow different buggies to be created</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-DEL Allow buggies to be deleted</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-FLAG Display the pennant graphically</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>3-TESTS Write some tests</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>4-USERS Add users (and sessions) so you know who is editing a buggy</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>4-REGISTER Make a new user</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>4-OWNER A buggy belongs to a user</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>4-PASS Add password protection to the users</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>5-VIZ Visual representation of the buggy</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>5-RESET Password reset</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>5-RACELOG Store a history of race results for the buggies in your app</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>5-ADMIN Add admin capabilities to superusers</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>5-API Use the server API for submitting the buggy data</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

```html
<div class="task">
  <h2>6-FREE Add custom features to the editor</h2>
  <p>
    <!-- sentence on _how_ you fixed it -->
  </p>
  <p>
    <!-- sentence(s) on anything interesting/incomplete you did -->
  </p>
</div>
```

<!-- POSTER-TASK-HTML-END -->
{% include footer.html %}
