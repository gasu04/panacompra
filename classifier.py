from nltk import decorators
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num
from matplotlib import rc
from modules import db_worker
from sqlalchemy.orm import undefer
from nltk import FreqDist
from datetime import date, timedelta
import nltk
import pprint

stemmer_func = nltk.stem.snowball.SpanishStemmer().stem
stopwords = set(nltk.corpus.stopwords.words('spanish')).union({'de','para','la','en','y','con','par'})

@decorators.memoize
def normalize_word(word):
    return stemmer_func(word.lower().strip())

def load_words(filename):
    with open(filename) as f:
        words = {normalize_word(word) for word in f.readlines()}
    return words
 
def get_words(documents):
    words = [normalize_word(word) for document in documents for word in document.split()]
    return words
##
##def document_features(document):
##    document_words = set(document)
##    features = {}
##    return features

def document_features(document,word_features):
    if document is None:
        document = ''
    document = document.split()
    features = {
        'quimicos':any([word in quimicos for word in document]),
        'farmaco':any([normalize_word(word) in farmacos for word in document]),
        'herramienta':any([normalize_word(word) in herramientas for word in document]),
        'antibiotico':any([normalize_word(word) in antibioticos for word in document]),
        'agua':any([normalize_word(word) == 'agu' for word in document]),
        'marcapaso':any([normalize_word(word) == 'marcapas' for word in document]),
        'reactivos':any([normalize_word(word) == 'reactiv' for word in document]),
        'pediatria':any([normalize_word(word) == 'pediatr' for word in document]),
        'neonato':any([normalize_word(word) == 'neonat' for word in document]),
        'protesis':any([normalize_word(word) == 'protesis' for word in document]),
        'mediamentos':any([normalize_word(word) == 'medicament' for word in document]),
        'laboratorio':any([normalize_word(word) == 'laboratori' for word in document]),
        'equipo':any([normalize_word(word) == 'equip' for word in document]),
        'sistema':any([normalize_word(word) == 'sistem' for word in document]),
        'filtro':any([normalize_word(word) == 'filtr' for word in document]),
        'sensor':any([normalize_word(word) == 'sensor' for word in document]),
        }
    for word in document:
        features['contains(%s)' % normalize_word(word)] = (word in word_features)
    return features
#

def train_classifier():
    with open('supplies.txt') as s,open('pharma.txt') as p,open('equipment.txt') as e:
        documents = (
        [(document, 'supply') for document in s.readlines()] + 
        [(document, 'pharma') for document in p.readlines()] +
        [(document, 'equipment') for document in e.readlines()]
        )
    word_features = get_words([doc for doc,c in documents])
    train_set = [(document_features(document,word_features),c) for (document,c) in documents]
    classifier = nltk.NaiveBayesClassifier.train(train_set)
    return classifier,word_features

def sum_compras(x):
    if isinstance(x,list):
        return sum(map(sum_compras,x))
    else:
        return x.precio 

def plot_precio_fecha_log(cache):
    plt.figure(1)
    labels = ['ro','bo','go']
    subplots = [141,142,143]
    compras = [zip(*[(compra.precio,compra.fecha) for compra in cache[key]]) for key in cache.keys()]
    for db,label,subplot,key in zip(compras,labels,subplots,cache.keys()):
        db = list(db)
        plt.subplot(subplot)
        plt.title(key)
        plt.yscale('log')
        plt.xticks([min(db[1])+timedelta(days=100),date(2013,1,1)],['2012','2013'])
        plt.plot(db[1],db[0],label)
        plt.ylim([0,100000000])
        if subplot != 141:
            plt.tick_params(axis='both',which='both',top='off',left='off',right='off',labeltop='off',labelleft='off',labelright='off')
    compras = [zip(*[(compra.precio,compra.fecha) for compra in cache[key]]) for key in cache.keys()]
    for db,label in zip(compras,labels):
        db = list(db)
        plt.subplot(144)
        plt.title('Combined')
        plt.yscale('log')
        plt.xticks([min(db[1])+timedelta(days=100),date(2013,1,1)],['2012','2013'])
        plt.tick_params(axis='both',which='both',top='off',left='off',right='off',labeltop='off',labelleft='off',labelright='off')
        plt.plot(db[1],db[0],label)
        plt.ylim([0,100000000])
    plt.show()
    plt.tick_params(axis='both',which='both',top='off',left='off',right='off',labeltop='off',labelleft='off',labelright='off')

if __name__ == '__main__':
    quimicos = load_words('quimicos.csv')
    farmacos = load_words('farmacos.csv')
    herramientas = load_words('herramientas.csv')
    antibioticos = load_words('antibioticos.csv')
    c,word_features = train_classifier()
    query = db_worker.query_css_minsa().options(undefer('description'))
    print(query.count())
    db = dict()
    for compra in query.all():
        classified = c.classify(document_features(compra.description,word_features))
        try:
            db[classified] += [compra]
        except KeyError:
            db[classified] = [compra]
    db_sum = {c:0 for c in db.keys()}
    db_sum = {c:db_sum[c] + sum_compras(db[old]) for c,old in zip(db_sum.keys(),db.keys())}
    pprint.pprint(db_sum)
    plot_precio_fecha_log(db)
