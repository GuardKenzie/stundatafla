from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import tafla
from datetime import date, datetime, time, timedelta
import random
import pandas as pd
import os

app = Flask(__name__)

# Time management

day_start = "08:20"
day_end   = "18:20"

day_start = datetime.strptime(day_start, "%H:%M")
day_end   = datetime.strptime(day_end, "%H:%M")

DAYDURATION = abs(day_end - day_start).seconds

# Background colours

background_colors = [
    "#e0af68",
    "#f7768e",
    "#9ece6a",
    "#73daca",
    "#7dcfff",
    "#bb9af7"
]

# File upload

UPLOADFOLDER = tafla.SHEETSFOLDER
ALLOWEDEXT   = ["xlsx"]

app.config["UPLOAD_FOLDER"] = UPLOADFOLDER


def getRuler(spacing=timedelta(minutes=30)):
    time_strings = []

    current = day_start
    while current <= day_end:
        time_strings.append(current.strftime("%H:%M"))
        current += spacing

    out = ["·"] * ((len(time_strings) - 1) * 3 + 1) 
    out[0::3] = time_strings

    return out


def allowed_filename(filename):
    dot_in_name  = "." in filename
    extension_ok = filename.split(".")[-1] in ALLOWEDEXT

    return dot_in_name and extension_ok

@app.route("/")
@app.route("/<int:year>/<int:month>/<int:day>")
def tableDelta(year=None, month=None, day=None):

    if year is None or month is None or day is None:
        date = datetime.now()
    else:
        date = datetime(year, month, day)

    dagur = tafla.fetchDay(date, discard_hidden=True)

    # calculate margins
    last_margin = 0
    for c in dagur.classes:
        c.top_margin = 100 * abs(day_start - c.start).seconds / DAYDURATION
        c.top_margin -= last_margin

        last_margin  = 100 * abs(day_start - c.end).seconds / DAYDURATION
        c.height = 100 * c.duration().seconds / DAYDURATION
    
    next_day = date + timedelta(days=1)
    next_day = {
        "year":  next_day.year, 
        "month": next_day.month, 
        "day":   next_day.day
    }

    prev_day = date - timedelta(days=1)
    prev_day = {
        "year":  prev_day.year, 
        "month": prev_day.month, 
        "day":   prev_day.day
    }

    print(date + timedelta(days=1))

    context = {
        "next_date":        next_day,
        "prev_date":        prev_day,
        "ruler":            getRuler(timedelta(hours=1)),
        "dags":             date, 
        "classes":          dagur.classes, 
        "day_duration":     DAYDURATION,
        "background_color": random.choice(background_colors),
        "title":            date.strftime("%A - %d. %B")
    }
    
    return render_template("day_view.html", **context)

@app.route("/manage")
def manage():
    out = ""
    dagar = tafla.fetchWeek(datetime.now() + tafla.TIMEPADDING)[0:5]

    context = {
        "dagar": dagar,
        "background_color": random.choice(background_colors)
    }

    return render_template("manage.html", **context)


@app.route("/hide", methods=["POST"])
def hideClass():
    out = tafla.hideClass(request.get_json())

    return out


@app.route("/upload", methods=["POST"])
def uploadTable():
    if request.method == "POST":
        # check if we gots file
        if "file" not in request.files:
            return "No file"
        
        file = request.files["file"]

        if file.filename == "":
            return "Invalid filename"

        if file and allowed_filename(file.filename):
            abs_upload_path = os.path.join(UPLOADFOLDER, "report.xlsx")

            file.save(abs_upload_path)

            # add hidden column
            stundatafla = pd.read_excel(abs_upload_path)
            stundatafla["hidden"] = 0
            stundatafla.to_csv(os.path.join(UPLOADFOLDER, "tafla.csv"), index=False)

            # remove old shitty excel sheet
            os.remove(os.path.join(UPLOADFOLDER, "report.xlsx"))

            return redirect(url_for("manage"))


    return

