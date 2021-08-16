import pandas as pd
from datetime import datetime, time, timedelta
import re
import json
import os
from flask import Flask

app = Flask(__name__)

DEBUG = app.config["DEBUG"]

DATEFORMAT = "%Y-%m-%d %H:%M:%S"
TIMEPADDING = timedelta(days=20)

if DEBUG:
    SHEETSFOLDER = "sheets"
    SHEETNAME = "tafla.csv"
else:
    SHEETSFOLDER = "/var/www/mage.black/tafla/sheets/"
    SHEETNAME    = "tafla.csv"

SHEETLOC     = os.path.join(SHEETSFOLDER, SHEETNAME)
#TAFLALOC = "sheets/report.xlsx"

"""
Format:
Dags.   Frá     til     Bygging     Staður      Hópur   Kennarar
"""

name_regex = r"(\w\w\w\d{3}\w)-\d+ (.+)$"

class Timi:
    def __init__(self, start, end, weekday, class_name, location, class_type, hidden=False):
        self.start      = datetime.strptime(str(start).zfill(4), "%H%M")
        self.end        = datetime.strptime(str(end).zfill(4),   "%H%M")
        self.weekday    = weekday

        self.hidden = hidden

        split_name = re.findall(name_regex, class_name)[0]

        self.hopur      = class_name
        self.name       = split_name[1]
        self.id         = split_name[0]

        self.location   = location
        self.type       = class_type
        self.top_margin = 0
        self.height     = 0


    def __lt__(self, other):
        return self.start < other.start
    
    def __gt__(self, other):
        return self.start > other.start

    def __le__(self, other):
        return self.start <= other.start

    def __ge__(self, other):
        return self.start >= other.start

    def __eq__(self, other):
        start_same = self.start == other.start
        end_same   = self.end   == other.end

        id_same      = self.id      == other.id
        weekday_same = self.weekday == other.weekday

        return all([start_same, end_same, id_same, weekday_same])


    def duration(self) -> timedelta:
        return abs(self.end - self.start)

    def getStart(self) -> str:
        return self.start.strftime("%H:%M")

    def getEnd(self) -> str:
        return self.end.strftime("%H:%M")

    def getIdentifier(self):
        out = {
            "weekday": self.weekday,
            "start":   int(self.getStart().replace(":", "")),
            "hopur":   self.hopur
        }
        return json.dumps(out)


class Dagur:
    def __init__(self, classes):
        self.classes = sorted(classes)
    
    def starts(self):
        return min(self.classes).start.strftime("%H:%M")
    
    def ends(self):
        return max(self.classes).end.strftime("%H:%M")


def _parseTafla():
    if not os.path.isfile(SHEETLOC):
        return None
    
    stundatafla = pd.read_csv(SHEETLOC)
    stundatafla["Dags."] = stundatafla["Dags."].apply(lambda x: datetime.strptime(x, DATEFORMAT))

    return stundatafla

def getHiddenClasses():
    stundatafla = _parseTafla()

    if stundatafla is None:
        return []

    # Get hidden classes
    hidden_classes = stundatafla[stundatafla["hidden"] == True]

    out = []
    
    for _, row in hidden_classes.iterrows():
        timi = Timi(
            row["Frá"], 
            row['til'], 
            row["Dags."].weekday(), 
            row["Hópur"], 
            row["Staður"], 
            "F",
        )

        out.append(timi)

    return out


def hideClass(data):
    stundatafla = pd.read_csv(SHEETLOC)

    for i, row in stundatafla.iterrows():
        weekday = data["weekday"] == datetime.strptime(row["Dags."], DATEFORMAT).weekday()
        start   = data["start"]   == row["Frá"]
        hopur   = data["hopur"]   == row["Hópur"]

        if weekday and start and hopur:
            out = str(row)
            
            stundatafla.at[i, "hidden"] = (row["hidden"] + 1) % 2
            break
    
    stundatafla.to_csv(SHEETLOC, index=False)
    return out



def fetchWeek(date_to_fetch: datetime):
    stundatafla = _parseTafla()

    current_weekday = date_to_fetch.weekday()
    start_of_day = date_to_fetch.replace(hour=0, minute=0, second=0)

    # Last monday
    last_monday = start_of_day - timedelta(days=current_weekday)

    vika = [fetchDay(last_monday + timedelta(days=a)) for a in range(7)]

    return vika


def fetchDay(date_to_fetch: datetime, discard_hidden=False):
    stundatafla = _parseTafla()

    if stundatafla is None:
        return Dagur([])
    
    # hidden classes
    hidden_classes = getHiddenClasses()

    # Get day    
    start_of_day      = date_to_fetch.replace(hour=0, minute=0, second=0)
    start_of_next_day = date_to_fetch.replace(hour=0, minute=0, second=0) + timedelta(days=1)

    dagur = stundatafla[
        (start_of_day <= stundatafla["Dags."]) & 
        (stundatafla["Dags."] < start_of_next_day)
        ]

    # objectify
    out = []

    for _, line in dagur.iterrows():
        timi = Timi(
            line["Frá"], 
            line['til'], 
            line["Dags."].weekday(), 
            line["Hópur"], 
            line["Staður"], 
            "F",
        )

        timi.hidden = timi in hidden_classes

        # henda falinn out
        # 0     0      1
        # 0     1      1
        # 1     0      1
        # 1     1      0

        if not (discard_hidden and timi.hidden):
            out.append(timi)

    return Dagur(out)

if __name__ == "__main__":
    a = fetchDay(datetime.now() + timedelta(days=20))
    print(a.starts())
    print(a.ends())
