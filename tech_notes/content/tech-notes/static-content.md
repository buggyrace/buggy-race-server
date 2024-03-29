Title: static content


# Static content (e.g., adding images)

---

Your webserver serves a combination of [static and dynamic](static-vs-dynamic)
content. A lot of your focus has been in `app.py` where you have been
programming the dynamic content.

But you did edit some static content too: the style sheet `static/app.css`
is an example.

Images are another very common example of static content.


## How to add an image in Flask

Make sure that the file-size (bytes) of any images you serve on the web are no
bigger than they need to be. (Image compression is a superinteresting topic
but we don't get into that in Foundation, sorry).

Put the image in the `/static` directory (alongside `app.css`).

To add that image into your webpage, in the HTML use the 
[`<img>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img):

    <img src="/static/cat.gif" alt="cat typing on keyboard" />

If you need to style it, use CSS (of course) — ideally by editing the style
sheet (and maybe adding something like `class="images-of-cats"`) if you want to
style different kinds of image differently. It is common and correct to
position and resize images using CSS.

Remember that we have a tech note on
[how to add a cache-buster](cache-busting-css)
if your CSS changes aren't appearing in your browser after you have changed
the CSS file.


## Is dynamic content always HTML?

Absolutely not! You _could_ create your images or CSS dynamically if you needed
to.

For example, it's not uncommon for webservers to produce PDFs or graphics that
are dynamic (e.g., documents pre-filled with the user's details, or images
containing graph plots of data).

It's not so impressive, but when you pressed the "Get Buggy JSON" button, your
webserver was producing dynamic content that wasn't HTML. Instead of rendering
an HTML template, it ran Flask's `jsonify` function. Incidentally, not only did
that "make" the JSON, but it set the
[`Content-type`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type)
header for you (that's how the browser knew it wasn't HTML that it had got
back).

## Can you have a website that is _totally_ static?

Yes you can, and your looking at one now! (Well, probably — it depends a little
on how the race server was set up this time).

The tech notes pages you're looking at are just static HTML: there's nothing in
them that changes from request to request. If they _do_ change it will be because
we've changed the content in some way. When that happens, the site is
re-deployed. Specifically, they are  generated using
[Pelican](https://getpelican.com), which is written in Python.

In practice, this means most of the {{ PROJECT_CODE }} Tech Notes you're
reading are written as markdown and Jina templates (the same template
mechanism Flask uses). Pelican converts them into the HTML pages that end up
in your browser.

Static sites are popular because they are simple to run, can be optimised for
speed and [caching](cache-busting-css), and expose the server to fewer security
risks than dynamic sites do.

A basic static site can also be relatively straightforward to build. However,
generating a static site _can_ become a very sophisticated process — possibly
exploiting resources and time that you wouldn't have if you were trying to
serve it in real time — but the point is everything happens _before_ any HTTP
requests are being handled. By the time it's up on the webserver, all the work
is done.

## GitHub pages

We chose to build the tech notes pages with Pelican because it's a Python tool,
and the race server is already running Python. But previously we published them
as [GitHub Pages](https://pages.github.com). In that case, the deployment is
handled by [Jekyll](https://jekyllrb.com). Jekyll is a popular static site
generator (there are others) written in the programming language Ruby. 
GitHub Pages is a very convenient way to publish static sites — especially
documentation for open source projects. The content is written in
GitHub-flavoured [markdown](https://github.github.com/gfm/) and (of course)
stored in version control (Git). When the pages are updated, that change is
committed, and the repo pushed up to GitHub. This triggers Jekyll to rebuild
the website, turning the markdown into HTML and deploying it on the server.

