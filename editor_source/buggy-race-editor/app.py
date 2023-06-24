from flask import Flask, jsonify, render_template, request
import sqlite3 as sql

# the flask application: uses the webserver imported from the flask module:
app = Flask(__name__)

# constants: values that we need that won't change during the run:
DATABASE_FILE = "database.db"
DEFAULT_BUGGY_ID = "1"
BUGGY_RACE_SERVER_URL = "https://RACE-SERVER-URL"

#-----------------------------------------------------------------------------
# the home (or "index") page
#-----------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", server_url=BUGGY_RACE_SERVER_URL)

#-----------------------------------------------------------------------------
# creating a new buggy:
#  * if it's a GET request, just show the form
#  * but if it's a POST request, process the submitted data
#-----------------------------------------------------------------------------
@app.route("/new", methods=["POST", "GET"])
def create_buggy():
    if request.method == "GET":
        return render_template("buggy-form.html")
    elif request.method == "POST":
        message = ""
        qty_wheels = request.form["qty_wheels"]
        try:
            with sql.connect(DATABASE_FILE) as db_connection:
                cur = db_connection.cursor()
                cur.execute(
                    "UPDATE buggies set qty_wheels=? WHERE id=?",
                    (qty_wheels, DEFAULT_BUGGY_ID)
                )
                db_connection.commit()
        except sql.OperationalError as e:
            message = f"Error in update operation: {e}"
            db_connection.rollback()
        else:
            message = "Record successfully saved"
        finally:
            db_connection.close()
        return render_template("updated.html", msg=message)

#-----------------------------------------------------------------------------
# a page for displaying the buggy
#-----------------------------------------------------------------------------
@app.route("/buggy")
def show_buggies():
    db_connection = sql.connect(DATABASE_FILE)
    db_connection.row_factory = sql.Row
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM buggies")
    record = cur.fetchone(); 
    return render_template("buggy.html", buggy=record)

#-----------------------------------------------------------------------------
# get the JSON data that describes the buggy:
#  This reads the buggy record from the database, turns it into JSON format
#  (excluding any empty values), and returns it. There's no .html template
#  here because the response being sent only consists of JSON data.
#-----------------------------------------------------------------------------
@app.route("/json")
def send_buggy_json():
    db_connection = sql.connect(DATABASE_FILE)
    db_connection.row_factory = sql.Row
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM buggies WHERE id=? LIMIT 1", (DEFAULT_BUGGY_ID))
    buggies = dict(
      zip([column[0] for column in cur.description], cur.fetchone())
    ).items() 
    return jsonify(
        {key: val for key, val in buggies if not (val == "" or val is None)}
    )

#------------------------------------------------------------
# finally, after all the set-up above, run the app:
# This listens to the port for incoming HTTP requests, and sends a response
# back for each one. Unless something goes wrong, or you interrupt it (maybe
# with control-C), it will run forever... so any code you put _after_ app.run
# here won't normally be run.
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
