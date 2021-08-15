from flask import Flask, render_template, request, redirect, url_for
import tafla
from datetime import date, datetime, time, timedelta
import random

app = Flask(__name__)

day_start = "08:20"
day_end   = "18:20"

day_start = datetime.strptime(day_start, "%H:%M")
day_end   = datetime.strptime(day_end, "%H:%M")

DAYDURATION = abs(day_end - day_start).seconds

background_colors = [
    "#e0af68",
    "#f7768e",
    "#9ece6a",
    "#73daca",
    "#7dcfff",
    "#bb9af7"
]


def getRuler(spacing=timedelta(minutes=30)):
    time_strings = []

    current = day_start
    while current <= day_end:
        time_strings.append(current.strftime("%H:%M"))
        current += spacing

    out = ["·"] * ((len(time_strings) - 1) * 3 + 1) 
    out[0::3] = time_strings

    return out

@app.route("/")
@app.route("/<int:date_delta>")
def tableDelta(date_delta=0):
    date = datetime.now() + timedelta(days=date_delta)
    dagur = tafla.fetchDay(date, discard_hidden=True)

    # calculate margins
    last_margin = 0
    for c in dagur.classes:
        c.top_margin = 100 * abs(day_start - c.start).seconds / DAYDURATION
        c.top_margin -= last_margin

        last_margin  = 100 * abs(day_start - c.end).seconds / DAYDURATION
        c.height = 100 * c.duration().seconds / DAYDURATION
    
    context = {
        "next_date":        date_delta + 1,
        "prev_date":        max(0, date_delta - 1),
        "ruler":            getRuler(timedelta(hours=1)),
        "dags":             date, 
        "classes":          dagur.classes, 
        "day_duration":     DAYDURATION,
        "background_color": random.choice(background_colors),
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

