import json
import os
import pickle
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from buildrecs import closest_projects, vect, read_data
from collections import defaultdict
# from csv import DictReader
import random

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = ""  # "password"  # ""
MYSQL_PORT = 3306
MYSQL_DATABASE = "drinksdb"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)

# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this


feedback_likes = {}
feedback_dislikes = {}
input_likes = []
input_dislikes = []


def build_inverted_index(dict_reader):
    documents = defaultdict(list)
    for x in dict_reader:

        ingredient_list = x['ingredients1']+"," + x['ingredients2']+","+x['ingredients3']+","+x['ingredients4']+","+x['ingredients5']+","+x['ingredients6'] + \
            ","+x['ingredients7']+","+x['ingredients8']+","+x['ingredients9'] + \
            ","+x['ingredients10']+"," + \
            x['ingredients11']+","+x['ingredients12']

        documents[x['drink_name']].append(
            (ingredient_list.rstrip(','), x["instructions"], x["picture"], x["tags"]))

    return documents


query_sql = f"""SELECT * FROM drinks_table;"""

keys = ["id", "drink_name", "instructions", "steps", "picture", "tags", "ingredients1", "quantity1", "ingredients2",
        "quantity2", "ingredients3", "quantity3", "ingredients4", "quantity4", "ingredients5", "quantity5",
        "ingredients6", "quantity6", "ingredients7", "quantity7", "ingredients8", "quantity8", "ingredients9",
        "quantity9", "ingredients10", "quantity10", "ingredients11", "quantity11", "ingredients12", "quantity12"]

ingr_cols = ["ingredients1", "ingredients2", "ingredients3", "ingredients4", "ingredients5", "ingredients6", "ingredients7",
             "ingredients8", "ingredients9", "ingredients10", "ingredients11", "ingredients12"]

data = mysql_engine.query_selector(query_sql)

drinks_data = [dict(zip(keys, i)) for i in data]
projects_repr_in = vect(drinks_data[1:])
documents = read_data(drinks_data[1:])
inverted_idx = build_inverted_index(drinks_data[1:])


def boolean_not(dislikes):
    recs = []
    empty_dislikes = False
    # print("dislikes", dislikes)
    if (dislikes == [''] or dislikes == [] or dislikes == ""):
        empty_dislikes = True
    if (empty_dislikes):
        for x in drinks_data[1:]:
            ingredient_list = x['ingredients1']+" " + x['ingredients2']+" "+x['ingredients3']+" "+x['ingredients4']+" "+x['ingredients5']+" "+x['ingredients6'] + \
                " "+x['ingredients7']+" "+x['ingredients8']+" "+x['ingredients9'] + \
                " "+x['ingredients10']+" " + \
                x['ingredients11']+" "+x['ingredients12']

            recs.append((x["id"], x['drink_name'], ingredient_list.strip(
            ), x['picture'], x['instructions'], x['tags']))
    else:
        for dic in drinks_data[1:]:
            # print("drink:", dic["drink_name"])
            found_dislike = False
            for dislike in dislikes:
                if dislike != "" and dislike != " ":
                    curr_ingredients = []
                    for col in ingr_cols:
                        if dic[col] and dic[col] != "":
                            # print('ingr', dic[col])
                            curr_ingredients.append(dic[col])
                            if dislike in dic[col]:
                                # print("dislike found:", dislike)
                                found_dislike = True
            if found_dislike == False:
                recs.append((dic["id"], dic["drink_name"], curr_ingredients,
                            dic['picture'], dic['instructions'], dic['tags']))
    # print("recs in not", recs)
    return recs


def get_recs(likes, dislikes, get_most_similar):

    recs = boolean_not(dislikes)
    acc = []
    if likes == [''] or likes == []:  # user inputs no likes
        for rec in recs:
            acc.append({'id': rec[0], 'drink': rec[1], 'ingredients': ', '.join(
                rec[2]), 'picture': rec[3], 'instructions': rec[4], 'tags': rec[5]})
    else:
        set_likes = set(likes)
        for rec in recs:
            for like in set_likes:
                if like in rec[2]:
                    acc.append({'id': rec[0], 'drink': rec[1], 'ingredients': ', '.join(
                        rec[2]), 'picture': rec[3], 'instructions': rec[4], 'tags': rec[5]})
    highest_sim = []
    drink_sim = []
    for i in acc:
        project_index_in = i['id']
        for tup in closest_projects(project_index_in, projects_repr_in, documents):
            drink = tup[0]
            if (drink not in drink_sim):
                highest_sim.append(tuple(tup))
                drink_sim.append(drink)
        highest_sim.sort(key=lambda x: x[1], reverse=True)
        # highest_sim is the list of drinks and their sim score

    if (get_most_similar == '0'):
        highest_sim = highest_sim[:6]
    else:
        highest_sim = highest_sim[-6:]

    result = []
    for i, j in highest_sim:
        overlap = 0
        for like in input_likes:
            if like in inverted_idx[i][0][0]:
                overlap += 1
        for dislike in input_dislikes:
            if dislike not in inverted_idx[i][0][0]:
                overlap += 1

        liked_percent = overlap / (len(input_likes) + len(input_dislikes))
        merged_stars = round(5*(j + liked_percent)/2, 2)

        result.append({'drink': i, 'ingredients': inverted_idx[i][0][0], 'picture': inverted_idx[i]
                      [0][2], 'instructions': inverted_idx[i][0][1], 'tags': inverted_idx[i][0][3],
                      'merged_score': merged_stars})
    # print("results", result)
    return json.dumps(result)


@ app.route("/")
def home():
    return render_template('base.html', title="sample html")


@ app.route("/drinks_table")
def drinks_search():
    global input_likes, input_dislikes
    likes = request.args.get("likes")
    dislikes = request.args.get("dislikes")
    likes_list = likes.split(',')
    dislikes_list = dislikes.split(',')
    likes_list = [x.strip() for x in likes_list]
    dislikes_list = [x.strip() for x in dislikes_list]
    input_likes = likes_list
    input_dislikes = dislikes_list
    most_sim = request.args.get("most_sim")
    # print("most_sim", most_sim)
    return get_recs(likes_list, dislikes_list, most_sim)


@ app.route("/rocchio")
def rocchio_search():
    global feedback_likes, feedback_dislikes, input_likes, input_dislikes
    tags = request.args.get("tags").split(" ")
    likes = request.args.get("likes")
    drink_name = request.args.get("drink")
    ingredients = request.args.get("ingrs").split(",")

    if likes == 'true':
        feedback_likes[drink_name] = [tags, ingredients]
    if likes == 'false':
        feedback_dislikes[drink_name] = [tags, ingredients]

    # print("feedback", feedback_likes, feedback_dislikes)
    alpha = 1.5
    beta = 1.25
    gamma = 1.75
    new_query_dict = {}
    # print("inputs", input_likes, input_dislikes)
    feedback_liked_ingrs = []
    for val in feedback_likes.values():
        for ingr in val[1]:
            feedback_liked_ingrs.append(ingr)
            new_query_dict[ingr] = 0
    feedback_disliked_ingrs = []
    for val in feedback_dislikes.values():
        for ingr in val[1]:
            feedback_disliked_ingrs.append(ingr)
            new_query_dict[ingr] = 0

    # alpha part of rocchio computation
    for ingr in input_likes:
        new_query_dict[ingr] = alpha
    for ingr in input_dislikes:
        new_query_dict[ingr] = -1 * alpha

    # beta part of rocchio computation
    total_rel_drinks = len(feedback_likes) + 1
    for ingr in feedback_liked_ingrs:
        new_query_dict[ingr] += beta * (1/total_rel_drinks)
    # gamma part of rocchio computation
    total_nonrel_drinks = len(feedback_dislikes) + 1
    for ingr in feedback_disliked_ingrs:
        new_query_dict[ingr] -= gamma * (1/total_nonrel_drinks)

    new_feedback_liked_ingr = []
    new_feedback_disliked_ingr = []
    for ingr in new_query_dict:
        if new_query_dict[ingr] > 0:
            for _ in range(round(new_query_dict[ingr])):
                new_feedback_liked_ingr.append(ingr)
        if new_query_dict[ingr] < 0:
            for _ in range(round(new_query_dict[ingr])):
                new_feedback_liked_ingr.append(ingr)
            new_feedback_disliked_ingr.append(ingr)
    # print("new recs", new_feedback_liked_ingr, new_feedback_disliked_ingr)
    return get_recs(new_feedback_liked_ingr, new_feedback_disliked_ingr)


@ app.route("/boolean_and")
def boolean_and_search():
    likes = request.args.get("likes").split(", ")
    dislikes = request.args.get("dislikes").split(", ")
    recs = boolean_not(dislikes)
    acc = []
    recs_drink_name = []
    for drink in recs:
        recs_drink_name.append(drink[1])
    if likes != [''] or likes != []:  # user inputs no likes
        for dic in drinks_data[1:]:
            if (dic['drink_name'] in recs_drink_name):
                ingr = inverted_idx[dic['drink_name']][0][0].split(',')
                if len(set(likes) & set(ingr)) == len(likes):
                    acc.append({'drink': dic['drink_name'], 'ingredients': inverted_idx[dic['drink_name']][0][0], 'picture': inverted_idx[dic['drink_name']]
                                [0][2], 'instructions': inverted_idx[dic['drink_name']][0][1], 'tags': inverted_idx[dic['drink_name']][0][3],
                                'merged_score': '5'})
    result = acc[0:6]
    return json.dumps(result)


@app.route("/clusters")
def get_clusters():
    with open('drinks_clusters.pkl', 'rb') as f:
        cluster_dict = pickle.load(f)
    acc = []
    cluster_dict_inv = defaultdict(list)
    for key, val in sorted(cluster_dict.items()):
        cluster_dict_inv[val].append(key)
    for i in range(len(cluster_dict_inv)):
        drink_name = random.choice(cluster_dict_inv[i])
        acc.append({'drink': drink_name, 'ingredients': inverted_idx[drink_name][0][0], 'picture': inverted_idx[drink_name]
                    [0][2], 'instructions': inverted_idx[drink_name][0][1], 'tags': inverted_idx[drink_name][0][3], 'merged_score': '5'})
    return json.dumps(acc)


@app.route("/cluster_recs")
def drinks_you_might_like(drink_name):
    with open('drinks_clusters.pkl', 'rb') as f:
        cluster_dict = pickle.load(f)
        cluster_dict_inv = defaultdict(list)
    for key, val in sorted(cluster_dict.items()):
        cluster_dict_inv[val].append(key)
    cluster_label = cluster_dict[drink_name]
    similar_drinks_list = cluster_dict_inv[cluster_label]
    random.shuffle(similar_drinks_list)
    result = []
    # can change this number to the number of drinks you want to show
    # only returns the drink and the image for now
    for i in similar_drinks_list[:5]:
        result.append({'drink': i, 'picture': inverted_idx[i][0][2]})

    return json.dumps(result)


# app.run(debug=True)
