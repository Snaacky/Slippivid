import os
import random
import string
import sys

import dataset
from flask import Flask, redirect, render_template, request

app = Flask(__name__)
app.config["SECRET_KEY"] = "change me"
app.config["PORT"] = 3000
app.config["DEBUG"] = True
app.config["DOWNLOADS"] = "replays/"
db = dataset.connect('sqlite:///slippivid.db')

processing_queue = []
current_queue_item = None


@app.route("/")
def index():
    return render_template("index.htm")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return("This endpoint must be accessed via POST.")

    if request.method == "POST":
        if "file" not in request.files:
            return("An error occurred while processing your upload. Please try again.", 400)

        file = request.files["file"]

        if file.filename == "":
            return("An error occurred while processing your upload. Please try again.", 400)

        if file.filename.split(".")[1].lower() != "slp":
            return("That is not a Slippi replay file.", 403)

        if file:
            # TODO: Add check to make sure the file doesn't exist
            replay_id = "".join(random.choice(string.ascii_letters) for char in range(10))
            file.save(os.path.join(app.config["DOWNLOADS"], replay_id + ".slp" ))
            return redirect(f"/queue/{replay_id}")


@app.route("/queue/<replay_id>")
def queue(replay_id):
    table = db['replays']
    results = table.find_one(replay_id=replay_id)
    if results:
        return "found"
    else:
        table.insert(dict(replay_id=replay_id, streamable=None, progress=None))
        return "added"

    return render_template("queue.htm", replay_id=replay_id)


@app.route("/replay/<replay_id>")
def replay(replay_id):
    return render_template("replay.htm", replay_id=replay_id)


@app.errorhandler(404)
def file_not_found(error_code):
    return render_template('404.htm'), 404


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"])
