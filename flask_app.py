
# A very simple Flask Hello World app for you to get started with...

from datetime import datetime

from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


@app.route("/")
def home():
    return render_template("index.html", site_name="New P")


@app.route("/about")
def about():
    return render_template("about.html", site_name="New P")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

