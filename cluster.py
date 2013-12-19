from modules import db_worker
from sqlalchemy.orm import undefer
import numpy
from nltk.cluster import KMeansClusterer, GAAClusterer, euclidean_distance
from nltk import FreqDist
import nltk.corpus
from nltk import decorators
import nltk
from time import sleep
 
stemmer_func = nltk.stem.snowball.SpanishStemmer().stem
stopwords = set(nltk.corpus.stopwords.words('spanish')).union({'de','para','la','en','y','con','par'})
 
@decorators.memoize
def normalize_word(word):
    return stemmer_func(word.lower())
 
def get_words(documents):
    words = {normalize_word(word) for document in documents for word in document.split()}
    return list(words)
 
@decorators.memoize
def vectorspaced(document):
    document_components = [normalize_word(word) for word in document.split() if word not in stopwords]
    return numpy.array([word in document_components and not word in stopwords for word in words], numpy.short)
 
if __name__ == '__main__':
 
    nclusters = 15
    query = db_worker.query_css_minsa().options(undefer('description')).limit(3000)
    compras,documents = zip(*[(compra,compra.description) for compra in query.all()])
    print('got docs')
    words = get_words(documents)
    print('got words')

#    cluster = KMeansClusterer(nclusters, euclidean_distance)
    cluster = GAAClusterer(nclusters)
    cluster.cluster([vectorspaced(document) for document in documents if document])
    classified_examples = [(compra,cluster.classify(vectorspaced(document))) for compra,document in zip(compras,documents)]


    ## dict of { cluster:sum(price of compras in cluster) for cluster in cluster }
    clusters = { i:{'price':0} for i in range(nclusters) }
    for compra,cluster_id in classified_examples:
        clusters[cluster_id]['price'] = clusters[cluster_id]['price'] + compra.precio


    #m = max(clusters.keys(),key=lambda x: clusters[x]) #get max price cluster
    #print freqdist > 4
    for m in range(nclusters):
        dist = []
        for compra,cluster in filter(lambda x: x[1] == m,classified_examples):
            dist.extend([normalize_word(word) for word in compra.description.split() if word not in stopwords and normalize_word(word) not in stopwords])
        clusters[m]['dist'] = FreqDist(dist)

    for key in clusters.keys():
        print("cluster: %i (%d)" % (key, clusters[key]['price']))
        for w,f in clusters[key]['dist'].items():
            if f > 4:
                print('\t',w,f)
