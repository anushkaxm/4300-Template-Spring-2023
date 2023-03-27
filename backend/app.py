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


def sql_search(likes, dislikes):
    # query_sql = f"""SELECT * FROM mytable where LOWER( drink_name ) LIKE '%%{drink.lower()}%%' limit 5"""
    query_sql = f"""SELECT * FROM drinks_table;"""
    keys = ["id", "drink_name", "ingredients1", "ingredients2", "ingredient3",
            "ingredients4", "ingredients5", "ingredient6", "ingredients7", "ingredients8", "ingredient9",
            "ingredients10", "ingredients11", "ingredient12"]
    data = mysql_engine.query_selector(query_sql)
    # drinks_data = json.dumps([dict(zip(keys, i)) for i in data])
    drinks_data = [dict(zip(keys, i)) for i in data]
    # likes = drink[0]
    # dislikes = drink[1]
    recs = []
    for dislike in dislikes:
        for dic in drinks_data[1:]:
            curr_ingredients = [dic["ingredients1"], dic["ingredients2"], dic["ingredient3"], dic["ingredients4"], dic["ingredients5"], dic["ingredient6"],
                                dic["ingredients7"], dic["ingredients8"], dic["ingredient9"], dic["ingredients10"], dic["ingredients11"], dic["ingredient12"]]
            if (dislike not in curr_ingredients):
                recs.append((dic["drink_name"], curr_ingredients))
    acc = []
    if likes == []:  # user inputs no likes
        for rec in recs:
            acc.append({'drink': rec[0], 'ingredients': ' '.join(rec[1])})
    else:
        set_likes = set(likes)
        ingredients = set()
        for rec in recs:
            ingredients = set(rec[1])
            if (len(set_likes.intersection(ingredients)) > 0):
                acc.append({"drink": rec[0], "ingredients": ' '.join(rec[1])})
    return json.dumps(acc[:5])
# return json.dumps({"likes": drink[0], "dislikes": drink[1]})


@ app.route("/")
def home():
    return render_template('base.html', title="sample html")


@ app.route("/drinks_table")
def drinks_search():
    text = request.args.get("title")
    # t2 = request.args.get("dislikes")
    likes_dislikes = text.split()
    likes = likes_dislikes[0].split(',')
    dislikes = likes_dislikes[1].split(',')
    # likes = request.args.get("likes")
    # dislikes = request.args.get("dislikes")
    print(likes, dislikes)
    return sql_search(likes, dislikes)


# app.run(debug=True)
