import pandas as pd
from datetime import datetime, time, timedelta
import re

DATEFORMAT = "%Y-%m-%d %H:%M:%S"
TIMEPADDING = timedelta(days=20)

"""
Format:
Dags.   Frá     til     Bygging     Staður      Hópur   Kennarar
"""

name_regex = r"(\w\w\w\d{3}\w)-\d+ (.+)$"

class Timi:
    def __init__(self, start, end, class_name, location, class_type, hidden=False):
        self.start      = datetime.strptime(str(start).zfill(4), "%H%M")
        self.end        = datetime.strptime(str(end).zfill(4),   "%H%M")

        self.hidden = hidden

        print(class_name)
        split_name = re.findall(name_regex, class_name)[0]
        print(split_name)

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

    def duration(self) -> timedelta:
        return abs(self.end - self.start)

    def getStart(self) -> str:
        return self.start.strftime("%H:%M")

    def getEnd(self) -> str:
        return self.end.strftime("%H:%M")

class Dagur:
    def __init__(self, classes):
        self.classes = sorted(classes)
    
    def starts(self):
        return min(self.classes).start.strftime("%H:%M")
    
    def ends(self):
        return max(self.classes).end.strftime("%H:%M")


def _parseTafla():
    stundatafla = pd.read_excel("sheets/report.xlsx")
    stundatafla["Dags."] = stundatafla["Dags."].apply(lambda x: datetime.strptime(x, DATEFORMAT))

    return stundatafla

def getUnique():
    stundatafla = _parseTafla()

    return list(stundatafla["Hópur"].unique())


def fetchWeek(date_to_fetch: datetime):
    stundatafla = _parseTafla()

    current_weekday = date_to_fetch.weekday()
    start_of_day = date_to_fetch.replace(hour=0, minute=0, second=0)

    # Next monday
    days_until_next_monday = timedelta(days=(6 - current_weekday))
    next_monday = start_of_day + days_until_next_monday

    # Last monday
    last_monday = start_of_day - timedelta(days=current_weekday)

    vika = stundatafla[
        (last_monday <= stundatafla["Dags."]) & 
        (stundatafla["Dags."] < next_monday)
        ]

    return vika

def fetchDay(date_to_fetch: datetime, hidden_classes=[]):
    stundatafla = _parseTafla()

    # Get day    
    start_of_day      = date_to_fetch.replace(hour=0, minute=0, second=0)
    start_of_next_day = date_to_fetch.replace(hour=0, minute=0, second=0) + timedelta(days=1)

    dagur = stundatafla[
        (start_of_day <= stundatafla["Dags."]) & 
        (stundatafla["Dags."] < start_of_next_day)
        ]
    
    out = []

    # objectify
    for _, line in dagur.iterrows():
        name_of_class = re.findall(name_regex, line["Hópur"])

        if name_of_class and name_of_class[0][0] in hidden_classes:
            hidden = True
        else:
            hidden = False

        out.append(Timi(line["Frá"], line['til'], line["Hópur"], line["Staður"], "F", hidden=hidden))

    return Dagur(out)

if __name__ == "__main__":
    a = fetchDay(datetime.now() + timedelta(days=20))
    print(a.starts())
    print(a.ends())
