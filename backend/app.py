import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "drinksdb"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this


def sql_search(drink):
    # query_sql = f"""SELECT * FROM episodes WHERE LOWER( title ) LIKE '%%{episode.lower()}%%' limit 10"""
    # query_sql = f"""SELECT * FROM mytable where LOWER( drink_name ) LIKE '%%{drink.lower()}%%' limit 5"""
    query_sql = f"""SELECT * FROM mytable"""
    # keys = ["id","title","descr"]
    keys = ["FIELD1", "drink_name", "ingredients",
            "quantities", "instructions"]
    data = mysql_engine.query_selector(query_sql)
    # drinks_data = json.dumps([dict(zip(keys, i)) for i in data])
    drinks_data = [dict(zip(keys, i)) for i in data]
    likes = drink[0]
    dislikes = drink[1]
    recs = []
    for dislike in dislikes:
        for i, drink in enumerate(drinks_data["drink_name"]):
            if (dislike not in drinks_data["ingredients"][i]):
                recs.append((drink, drinks_data["ingredients"][i]))
    acc = []
    set_likes = set(likes)
    for rec in recs:
        ingredients = set(recs[1])
        if (len(set_likes.union(ingredients)) > 0):
            acc.append(rec)
    return acc


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/episodes")
def drinks_search():
    text = request.args.get("title")
    likes_dislikes = text.split()
    likes = likes_dislikes[0].split(',')
    dislikes = likes_dislikes[1].split(',')
    return sql_search((likes, dislikes))


app.run(debug=True)
