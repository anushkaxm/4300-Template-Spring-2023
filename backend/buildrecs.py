import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.linalg import svds
from sklearn.preprocessing import normalize


def read_data(rec):
    doc = []
    for x in rec:
        ingredient_list = x['ingredients1']+" " + x['ingredients2']+" "+x['ingredients3']+" "+x['ingredients4']+" "+x['ingredients5']+" "+x['ingredients6'] + \
            " "+x['ingredients7']+" "+x['ingredients8']+" "+x['ingredients9'] + \
            " "+x['ingredients10']+" " + \
            x['ingredients11']+" "+x['ingredients12']

        doc.append((x['drink_name'], ingredient_list.strip()))

    return doc


def vect(rec):

    documents = read_data(rec)

    vectorizer = TfidfVectorizer(stop_words='english', max_df=.7, min_df=50)
    td_matrix = vectorizer.fit_transform(x[1] for x in documents)
    # print(td_matrix.shape)

    # do SVD with a very large k (we usually use 100), just for the sake of getting many sorted singular values (aka importances)
    u, s, v_trans = svds(td_matrix, k=6)

    docs_compressed, s, words_compressed = svds(td_matrix, k=6)
    words_compressed = words_compressed.transpose()

    word_to_index = vectorizer.vocabulary_
    # index_to_word = {i:t for t,i in word_to_index.items()}

    # words_compressed_normed = normalize(words_compressed, axis = 1)

    td_matrix_np = td_matrix.transpose().toarray()
    td_matrix_np = normalize(td_matrix_np)

    docs_compressed_normed = normalize(docs_compressed)
    return docs_compressed_normed


def closest_projects(project_index_in, project_repr_in, documents):
    k = 5
    sims = project_repr_in.dot(project_repr_in[project_index_in, :])
    asort = np.argsort(-sims)[:k+1]
    print(asort)
    return [(documents[i][0], sims[i]) for i in asort[1:]]
