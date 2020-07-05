"""
user uploads file
upload generates random file name and saves
upload redirects user to /queue/<filename>
queue checks if file is in db and adds a row if it doesn't
queue_worker checks every 5 seconds to see if there is anything in queue
if nothing currently processing something in queue, set first item to current_queue_item
"""

import json
import os
import random
import string
import subprocess
import sys

import dataset
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, render_template, request

# Flask variables and config variables
app = Flask(__name__)
app.config["SECRET_KEY"] = "change me"
app.config["PORT"] = 3000
app.config["DEBUG"] = True
app.config["DOWNLOADS"] = "replays/"
app.config["DOLPHIN_BIN"] = "D:\\Programming\\slippivid\\FM-v5.9-Slippi-r18-Win\\Dolphin.exe"
app.config["MELEE_ISO"] = "D:\\Games\\ISOs and ROMs\\NGC\\Super Smash Bros. Melee.gcm"


# Database
db = dataset.connect('sqlite:///slippivid.db')

# Slippivid queue variables
replay_queue = []
current_queue_item = None


@app.route("/")
def index():
    # Renders the index template.
    return render_template("index.htm")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        # A user most likely tried to manually access the endpoint.
        return("This endpoint must be accessed via POST.")

    if request.method == "POST":
        if "file" not in request.files:
            # There was no file attached to the form.
            return("An error occurred while processing your upload. Please try again.", 400)

        file = request.files["file"]  # A file was attached to the form.

        if file.filename == "":
            # The file attached to the form had a blank username.
            return("An error occurred while processing your upload. Please try again.", 400)

        if file.filename.split(".")[1].lower() != "slp":
            # The file attached to the form was not a Slippi replay.
            return("That is not a Slippi replay file.", 403)

        if file:
            # A (presumably) valid replay was found. Saves to file system under
            # a randomly generated file name and returns to the queue page.
            # TODO: Add check to make sure the file doesn't exist
            replay_id = "".join(random.choice(string.ascii_letters) for char in range(10))
            file.save(os.path.join(app.config["DOWNLOADS"], replay_id + ".slp" ))
            return redirect(f"/queue/{replay_id}")


@app.route("/queue/<replay_id>")
def queue(replay_id):
    # Sets up table, ensures it exists if it didn't before.
    table = db['replays']
    # Checks to see if the ID passed already exists in the database.
    results = table.find_one(replay_id=replay_id)
    if not results: 
        # Creates a row in the database that didn't exist previously.
        table.insert(dict(replay_id=replay_id, streamable=None, progress=None))
    # Adds the replay to the queue for processing.
    replay_queue.append(replay_id)

    return render_template("queue.htm", replay_id=replay_id)


@app.route("/replay/<replay_id>")
def replay(replay_id):
    # Returns the replay template with the replay called in the URL arguments.
    return render_template("replay.htm", replay_id=replay_id)


@app.errorhandler(404)
def file_not_found(error_code):
    # Returns the 404 template with status 404 when unable to find route.
    return render_template('404.htm'), 404


def queue_worker():
    global current_queue_item
    # A replay is currently being processed.
    if current_queue_item != None:
        return

    # The queue is currently empty and nothing is being processed.
    if current_queue_item == None and len(replay_queue) == 0:
        return

    current_queue_item = replay_queue[0]
    generate_com_file(current_queue_item)
    test_dolphin(current_queue_item)
    return

def generate_com_file(replay_id):
    com = {
        "mode": "normal", 
        "replay": os.path.join(app.config["DOWNLOADS"], replay_id + ".slp"), 
        "isRealTimeMode": False,
        "commandId": replay_id}

    with open(f"com-{replay_id}.json", "w") as f:
        f.write(json.dumps(com))


def test_dolphin(replay_id):
    arguments = [
        app.config["DOLPHIN_BIN"],
        "-i", f"com-{replay_id}.json",
        "-e", app.config["MELEE_ISO"]
    ]
    subprocess.Popen(args=arguments)


# Sets up the scheduler to check for queue files to process.
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(queue_worker, "interval", seconds=5)
scheduler.start()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"])
