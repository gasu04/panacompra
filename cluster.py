from modules import db_worker

import numpy
from nltk.cluster import KMeansClusterer, GAAClusterer, euclidean_distance
from nltk import FreqDist
import nltk.corpus
from nltk import decorators
import nltk
from time import sleep
 
stemmer_func = nltk.stem.snowball.SpanishStemmer().stem
stopwords = set(nltk.corpus.stopwords.words('spanish'))
 
@decorators.memoize
def normalize_word(word):
    return stemmer_func(word.lower())
 
def get_words(documents):
    words = {normalize_word(word) for document in documents for word in document.split()}
    return list(words)
 
@decorators.memoize
def vectorspaced(document):
    document_components = [normalize_word(word) for word in document.split()]
    return numpy.array([word in document_components and not word in stopwords for word in words], numpy.short)
 
if __name__ == '__main__':
 
    query = db_worker.query_css_minsa()
    compras,documents = zip(*[(compra,compra.description) for compra in query.all()])
    print('got docs')
    words = get_words(documents)
    print('got words')

    cluster = KMeansClusterer(15, euclidean_distance)
#    cluster = GAAClusterer(10)
    cluster.cluster_vectorspace([vectorspaced(document) for document in documents if document])
    classified_examples = [(compra,cluster.classify(vectorspaced(document))) for compra,document in zip(compras,documents)]


    ## dict of { cluster:sum(price of compras in cluster) for cluster in cluster }
    clusters = { i:0 for i in range(15) }
    for compra,cluster_id in classified_examples:
        clusters[cluster_id] = clusters[cluster_id] + compra.precio


    m = max(clusters.keys(),key=lambda x: clusters[x]) #get max price cluster
    #print freqdist > 4
    dist = []
    for compra,cluster in filter(lambda x: x[1] == m,classified_examples):
        dist.extend([normalize_word(word) for word in compra.description.split() if word not in stopwords])
    for f,w in FreqDist(dist).items():
        if w > 4:
            print(f,w)
