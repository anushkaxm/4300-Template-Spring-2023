# import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
import pickle
from csv import DictReader
# open file in read mode

# should probably also add tags


def get_documents():
    with open("tags.csv", 'r') as f:
        dict_reader = DictReader(f)
        documents = []
        for x in dict_reader:
            ingredient_tag_list = x['ingredients1']+" " + x['ingredients2']+" "+x['ingredients3']+" "+x['ingredients4']+" "+x['ingredients5']+" "+x['ingredients6'] + \
                " "+x['ingredients7']+" "+x['ingredients8']+" "+x['ingredients9'] + \
                " "+x['ingredients10']+" " + \
                x['ingredients11']+" "+x['ingredients12']+" "+x['tags']

            documents.append(
                (x['drink_name'], ingredient_tag_list.strip()))
    return documents


def vect(documents):
    vectorizer = TfidfVectorizer(stop_words='english', max_df=.7, min_df=50)
    td_matrix = vectorizer.fit_transform(x[1] for x in documents)
    # word_to_index = vectorizer.vocabulary_
    td_matrix_np = td_matrix.toarray()
    return td_matrix_np


def pickle_clusters():
    documents = get_documents()
    vector = vect(documents)
    kmeans = KMeans(n_clusters=10)
    label = kmeans.fit_predict(vector)

    cluster_dictionary = {}
    for i in range(len(label)):
        cluster_dictionary[documents[i][0]] = label[i]
    with open('drinks_clusters.pkl', 'wb') as f:
        pickle.dump(cluster_dictionary, f)
