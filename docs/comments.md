---
title: comments
---

{% include common.html %}

# Comments in your webserver


---

You already know that comments are a really way to drop notes into your code.

A more technical way to understand them is that comments are effectively a way
to remove the comment text from the language parser. The parser is the process
which breaks down your code into _tokens_ based on the syntax of the language.
A good programmer needs to understand this: it's how you don't accidentally
comment-out things like closing tags or brackets, or try to put comments inside
strings.

Comments can be very helpful as debugging placeholders, explainers as to _why_
code is a particular way, or as documentation (many languages have automated
ways to extract comments into project documentation: if you're interested in
this for Python, see [pydoc](https://docs.python.org/3/library/pydoc.html)).

In your buggy editor webserver, there are two primary places you'll encounter
comments (and write your own): Python and HTML.

## Comments in Python

Comments in Python start with a `#` and continue to the end of the line. This
is why you can add comments on the same line as a statement:

```python

# this is a comment
# and so is this
#-----------------------------------

buggy = cur.fetchone()  # just get one of the records we've read


```

## Comments in HTML

Comments in HTML start with `<!--` and continue over as many lines as it takes
until `-->` turns up. You **cannot** nest comments.

```html
<!--  this is a comment -->
<p>
  This is a paragraph.
  <!-- another comment -->
</p>

<!--
    this is all a comment
    <p>
       so this paragraph will not display in the browser
       ...because it's inside the comment 
    </p>--> <p> I'm a paragraph</p>

<p>
  Another <!-- comment inside --> paragraph.
</p>
```

HTML comments are effectively at the element-level: as shown with the commented
`<p>` above, they can contain other elements, or (of course) appear _inside_
other elements' content... but don't use them to try to "comment-out"
attributes _within_ an element.



## Comments in other places

### Cascading style sheets (CSS)

Comments in **CSS** start with `/*` and end with `*/` and can run over many
lines.

```css
/* this is a comment 
   which may go over several
   lines */

h1 {
  color: red;  /* this is a comment  */
}
h2 { color: blue; }
```

### JavaScript

There are two kinds of comment in JavaScript:

Anything after `//` is a comment until the end of the line.

Or anything between `/*` and `*/` is a comment over any number of lines.

```javascript
let greeting = 'hello'; // this is a comment
/* this is
   a comment too 
   greeting = "goodbye"
*/
console.log(greeting); // writes "hello" to the console
   
```

### SQL

Comments in SQL are preceded with two hyphens. Most of the SQL in your project
is actually being quoted by Python (with the sqlite `execute()` function)
so you might not come across a need for this:

```sql
-- this is inserting one record into the table
INSERT INTO buggies VALUES (qty_wheels) SET (4);
```



{% include footer.html %}
