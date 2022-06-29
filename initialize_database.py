import json
import sqlite3
import uuid

con = sqlite3.connect("server/db.sqlite")
cur = con.cursor()

with open("data/matches.json") as file:
    matches = json.loads(file.read())

for match in matches:
    cur.execute(
        f"""INSERT INTO matches VALUES (
            '{str(uuid.uuid4())}',
            '{match["group_name"]}',
            '{match["teams"][0]}',
            '{match["teams"][1]}'
        )"""
    )

con.commit()

con.close()
