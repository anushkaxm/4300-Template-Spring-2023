import json
import os
import pickle
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from buildrecs import closest_projects, vect, read_data, closest_projects_to_query
from collections import defaultdict
import random

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = "password"  #
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


@ app.route("/drinks_table")
def drinks_search():
    global input_likes, input_dislikes, drinks_data, words_compressed, projects_repr_in, documents, inverted_idx
    likes = request.args.get("likes")
    dislikes = request.args.get("dislikes")
    # likes_list = likes.split(',')
    # dislikes_list = dislikes.split(',')
    # likes_list = [x.strip().lower() for x in likes_list]
    # dislikes_list = [x.strip().lower() for x in dislikes_list]
    input_likes = [likes]
    input_dislikes = [dislikes]
    most_sim = request.args.get("most_sim")
    getnonalc = request.args.get("getnonalc")
    data = runquery(getnonalc)
    drinks_data = [dict(zip(keys, i)) for i in data]
    id_num = -1
    if getnonalc == '1':
        for data in drinks_data:
            data['id'] = id_num
            id_num += 1
    words_compressed, projects_repr_in = vect(drinks_data[1:], getnonalc)
    documents = read_data(drinks_data[1:])
    inverted_idx = build_inverted_index(drinks_data[1:])
    return get_recs(likes, dislikes, most_sim)


feedback_likes = {}
feedback_dislikes = {}
input_likes = []
input_dislikes = []
drinks_data = []
words_compressed = []
projects_repr_in = []
documents = []
inverted_idx = []


def build_inverted_index(dict_reader):
    documents = defaultdict(list)
    for x in dict_reader:

        ingredient_list = x['ingredients1']+", " + x['ingredients2']+", "+x['ingredients3']+", "+x['ingredients4']+", "+x['ingredients5']+", "+x['ingredients6'] + \
            ", "+x['ingredients7']+", "+x['ingredients8']+", "+x['ingredients9'] + \
            ", "+x['ingredients10']+", " + \
            x['ingredients11']+", "+x['ingredients12']

        documents[x['drink_name']].append(
            (ingredient_list.rstrip(', '), x["instructions"], x["picture"], x["tags"]))

    return documents


def runquery(getnonalc):
    tag = 'nonalcoholic'
    if getnonalc == '1':
        query_sql = f"""SELECT * FROM drinks_table WHERE tags LIKE '%%{tag.lower()}%%';"""
    else:
        query_sql = f"""SELECT * FROM drinks_table;"""
    data = mysql_engine.query_selector(query_sql)
    return data


keys = ["id", "drink_name", "instructions", "steps", "picture", "tags", "ingredients1", "quantity1", "ingredients2",
        "quantity2", "ingredients3", "quantity3", "ingredients4", "quantity4", "ingredients5", "quantity5",
        "ingredients6", "quantity6", "ingredients7", "quantity7", "ingredients8", "quantity8", "ingredients9",
        "quantity9", "ingredients10", "quantity10", "ingredients11", "quantity11", "ingredients12", "quantity12"]

ingr_cols = ["ingredients1", "ingredients2", "ingredients3", "ingredients4", "ingredients5", "ingredients6", "ingredients7",
             "ingredients8", "ingredients9", "ingredients10", "ingredients11", "ingredients12"]


def boolean_not(dislikes):
    recs = []
    empty_dislikes = False
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
            found_dislike = False
            for dislike in dislikes:
                if dislike != "" and dislike != " ":
                    if dislike in inverted_idx[dic['drink_name'][0][0]] or dislike in dic['drink_name']:
                        found_dislike = True
            if found_dislike == False:
                recs.append((dic["id"], dic["drink_name"], inverted_idx[dic['drink_name']][0][0],
                            dic['picture'], dic['instructions'], dic['tags']))
    return recs


def get_recs(likes, dislikes, get_most_similar):

    if type(dislikes) == str:
        dislikes = dislikes.split(",")
    if type(likes) == str:
        likes = likes.split(",")

    if sorted(likes) == sorted(dislikes):  # both can't be empty or equal
        return json.dumps([])

    acc = []
    drink_sim = []
    highest_sim = []
    recs = boolean_not(dislikes)
    query = ""
    emptydislikes = False
    if (dislikes == [''] or dislikes == [] or dislikes == ""):  # no dislikes
        emptydislikes = True
        # don't use all recs, maybe try with current likes for drink_names
        # we still have some likes
        set_likes = set(likes)

        for like in set_likes:
            if like in list(inverted_idx.keys()):
                # is a drink_name
                acc.append({'id': list(inverted_idx.keys()).index(like), 'drink': like, 'ingredients': inverted_idx[like]
                            [0][0], 'picture': inverted_idx[like]
                            [0][2], 'instructions': inverted_idx[like][0][1], 'tags': inverted_idx[like][0][3]})
                # get drinks similar from this acc
            else:
                query += like+" "

    elif likes == [''] or likes == []:  # user inputs no likes:
        # accumulate on whatever user does not dislike in the dataset
        for rec in recs:
            acc.append({'id': rec[0], 'drink': rec[1], 'ingredients': inverted_idx[rec[1]]
                        [0][0], 'picture': rec[3], 'instructions': rec[4], 'tags': rec[5]})
    else:
        set_likes = set(likes)
        for rec in recs:
            for like in set_likes:
                if like in rec[2] or like in list(inverted_idx.keys()):
                    acc.append({'id': rec[0], 'drink': rec[1], 'ingredients': inverted_idx[rec[1]]
                               [0][0], 'picture': rec[3], 'instructions': rec[4], 'tags': rec[5]})
    if query != "":
        for tup in closest_projects_to_query(
                query, documents, words_compressed, projects_repr_in, get_most_similar):
            drink = tup[0]
            if (drink not in drink_sim):
                highest_sim.append(tuple(tup))
                drink_sim.append(drink)
    for i in acc:
        project_index_in = i['id']
        for tup in closest_projects(project_index_in, projects_repr_in, documents, get_most_similar):
            drink = tup[0]
            if (drink not in drink_sim and drink not in dislikes):
                highest_sim.append(tuple(tup))
                drink_sim.append(drink)

    # now do cosine similarity with all the dislikes again
    lowest_sim = []
    dislikes_acc = []
    dislikes_drinks = []
    if (not emptydislikes):
        for rec in recs:
            dislikes_acc.append({'id': rec[0], 'drink': rec[1], 'ingredients': inverted_idx[rec[1]]
                                 [0][0], 'picture': rec[3], 'instructions': rec[4], 'tags': rec[5]})

        for i in dislikes_acc:
            project_index_in = i['id']
            for tup in closest_projects(project_index_in, projects_repr_in, documents, get_most_similar):
                lowest_sim.append(tuple(tup))
                dislikes_drinks.append(tup[0])

    drink_list_with_scores = []
    for i, j in highest_sim:
        if i in dislikes_drinks:
            # remove dislikes from highest similarity list
            highest_sim.remove((i, j))

    if get_most_similar == '0':
        highest_sim.sort(key=lambda x: x[1], reverse=True)
        drink_list_with_scores = highest_sim[:6]
    else:
        if lowest_sim != []:
            lowest_sim.sort(key=lambda x: x[1])
            drink_list_with_scores = lowest_sim[:6]
        else:
            highest_sim.sort(key=lambda x: x[1])
            drink_list_with_scores = highest_sim[:6]

    # highest_sim = highest_sim[:6]

    result = []
    for i, j in drink_list_with_scores:
        overlap = 0
        for like in input_likes:
            if like in inverted_idx[i][0][0]:
                overlap += 1
        for dislike in input_dislikes:
            if dislike not in inverted_idx[i][0][0]:
                overlap += 1
        if (len(input_likes) + len(input_dislikes)) == 0:
            merged_stars = round(5*(j)*0.6, 2)
        else:
            liked_percent = overlap / (len(input_likes) + len(input_dislikes))
            merged_stars = round(5*(0.7*j + 0.3*liked_percent), 2)
            if merged_stars < 0:
                merged_stars = 0

        result.append({'drink': i, 'ingredients': inverted_idx[i][0][0], 'picture': inverted_idx[i]
                      [0][2], 'instructions': inverted_idx[i][0][1], 'tags': inverted_idx[i][0][3],
                      'merged_score': merged_stars})
    return json.dumps(result)


@ app.route("/")
def home():
    return render_template('base.html', title="sample html")


@ app.route("/rocchio")
def rocchio_search():
    global feedback_likes, feedback_dislikes, input_likes, input_dislikes
    tags = request.args.get("tags").split(" ")
    likes = request.args.get("likes")
    drink_name = request.args.get("drink")
    ingredients = request.args.get("ingrs").split(",")
    ingredients = [x.strip().lower() for x in ingredients]
    if likes == 'true':
        feedback_likes[drink_name] = [tags, ingredients]
    if likes == 'false':
        feedback_dislikes[drink_name] = [tags, ingredients]

    alpha = 1.5
    beta = 1.25
    gamma = 1.75
    new_query_dict = {}
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
    list_input_likes = input_likes
    if len(input_likes) == 1:
        list_input_likes[0].split(',')
    list_input_dislikes = input_dislikes
    if len(input_dislikes) == 1:
        list_input_dislikes = input_dislikes[0].split(',')
    for ingr in list_input_dislikes:
        new_query_dict[ingr] = alpha
    for ingr in list_input_dislikes:
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
    return get_recs(new_feedback_liked_ingr, new_feedback_disliked_ingr, '0')


@ app.route("/boolean_and")
def boolean_and_search():
    getnonalc = request.args.get("getnonalc")
    data = runquery(getnonalc)
    drinks_data = [dict(zip(keys, i)) for i in data]
    id_num = -1
    if getnonalc == '1':
        for data in drinks_data:
            data['id'] = id_num
            id_num += 1
    # words_compressed, projects_repr_in = vect(drinks_data[1:])
    # documents = read_data(drinks_data[1:])
    inverted_idx = build_inverted_index(drinks_data[1:])
    likes = request.args.get("likes").split(",")
    if (likes == ['']):
        return json.dumps([])

    likes = [drink.lower().strip() for drink in likes]
    dislikes = request.args.get("dislikes").split(",")
    dislikes = [drink.lower().strip() for drink in dislikes]
    recs = boolean_not(dislikes)
    acc = []
    recs_drink_name = []
    for drink in recs:
        recs_drink_name.append(drink[1])
    if likes != [''] or likes != []:  # user inputs no likes
        for dic in drinks_data[1:]:
            if (dic['drink_name'] in recs_drink_name):
                ingr = inverted_idx[dic['drink_name']][0][0].split(', ')
                if len(set(likes) & set(ingr)) == len(likes):
                    acc.append({'drink': dic['drink_name'], 'ingredients': inverted_idx[dic['drink_name']][0][0], 'picture': inverted_idx[dic['drink_name']]
                                [0][2], 'instructions': inverted_idx[dic['drink_name']][0][1], 'tags': inverted_idx[dic['drink_name']][0][3],
                                'merged_score': '5'})
    result = acc[0:6]
    return json.dumps(result)


@ app.route("/clusters")
def get_clusters():
    data = runquery('0')
    drinks_data = [dict(zip(keys, i)) for i in data]
    # words_compressed, projects_repr_in = vect(drinks_data[1:])
    # documents = read_data(drinks_data[1:])
    inverted_idx = build_inverted_index(drinks_data[1:])
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


@ app.route("/cluster_recs")
def drinks_you_might_like():
    data = runquery('0')
    drinks_data = [dict(zip(keys, i)) for i in data]
    # words_compressed, projects_repr_in = vect(drinks_data[1:])
    # documents = read_data(drinks_data[1:])
    inverted_idx = build_inverted_index(drinks_data[1:])
    drink_name = request.args.get("drink")
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
