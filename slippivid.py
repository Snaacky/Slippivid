from flask import Flask, redirect, render_template, request


app = Flask(__name__)
app.config["SECRET_KEY"] = "change me"
app.config["PORT"] = 3000
app.config["DEBUG"] = True


@app.route("/")
def index():
    return render_template("index.htm")


@app.errorhandler(404)
def file_not_found(error_code):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"])
