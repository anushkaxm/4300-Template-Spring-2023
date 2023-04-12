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
MYSQL_USER_PASSWORD = "password"
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
    keys = ["id", "drink_name", "instructions", "picture", "tags", "ingredients1", "quantity1", "ingredients2", 
    "quantity2", "ingredients3", "quantity3", "ingredients4", "quantity4", "ingredients5", "quantity5",
    "ingredients6", "quantity6", "ingredients7", "quantity7", "ingredients8", "quantity8", "ingredients9",
    "quantity9", "ingredients10", "quantity10", "ingredients11", "quantity11", "ingredients12", "quantity12"]

    ingr_cols = ["ingredients1", "ingredients2", "ingredients3", "ingredients4", "ingredients5", "ingredients6", "ingredients7",
    "ingredients8", "ingredients9", "ingredients10", "ingredients1", "ingredients12"]
    
    data = mysql_engine.query_selector(query_sql)
    # drinks_data = json.dumps([dict(zip(keys, i)) for i in data])
    drinks_data = [dict(zip(keys, i)) for i in data]
    # likes = drink[0]
    # dislikes = drink[1]
    recs = []
    for dislike in dislikes:
        for dic in drinks_data[1:]:
            curr_ingredients = []
            for col in ingr_cols:
                if dic[col] and dic[col] != "":
                    curr_ingredients.append(dic[col])
            if (dislike not in curr_ingredients):
                recs.append((dic["drink_name"], curr_ingredients, dic['picture'], dic['instructions']))
    #print("recs", recs[:2])
    acc = []
    if likes == ['']:  # user inputs no likes
        for rec in recs:
            print("rec1", rec[1], type(rec[1]))
            acc.append({'drink': rec[0], 'ingredients': ', '.join(rec[1]), 'picture': rec[2], 'instructions': rec[3]})
    else:
        set_likes = set(likes)
        ingredients = set()
        for rec in recs:
            ingredients = set(rec[1])
            if (len(set_likes.intersection(ingredients)) > 0):
                acc.append({"drink": rec[0], "ingredients": ', '.join(rec[1]), 'picture': rec[2], 'instructions': rec[3]})

    return json.dumps(acc[:5])
# return json.dumps({"likes": drink[0], "dislikes": drink[1]})


@ app.route("/")
def home():
    return render_template('base.html', title="sample html")


@ app.route("/drinks_table")
def drinks_search():
    # text = request.args.get("title")
    # t2 = request.args.get("dislikes")
    # likes_dislikes = text.split()
    likes = request.args.get("likes")
    dislikes = request.args.get("dislikes")
    likes_list = likes.split(',')
    dislikes_list = dislikes.split(',')
    likes_list = [x.strip() for x in likes_list]
    dislikes_list = [x.strip() for x in dislikes_list]
    print(likes_list, dislikes_list)
    return sql_search(likes_list, dislikes_list)


# app.run(debug=True)
