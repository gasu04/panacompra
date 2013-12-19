#!/usr/bin/python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import date2num
from matplotlib import rc
import matplotlib.cm as cm
from matplotlib.patches import Rectangle,Circle
import matplotlib.patheffects as PathEffects
import matplotlib.colors as mplcolor
from mpl_toolkits.mplot3d import Axes3D
from modules import db_worker
from time import sleep
from datetime import date
import random
import pprint
import locale
from datetime_truncate import truncate as trunc

query = db_worker.query_css_minsa()
hospitales = db_worker.hospitales()
font = {'family' : 'serif',
        'color'  : 'black',
        'weight' : 'normal',
        'size'   : 16,
        }

def plot_key_freq(cache,key,limit=1000000000):
    db = {}
    col = 2
    cache = list(cache)
    db = cache_to_dict(cache,key,limit)
    week = lambda x: trunc(x.fecha,'week')
    db = {k:cache_to_dict(db[k],week,limit) for k in db.keys()}
    plt.figure(figsize=(11,7))
    rows = round(len(db.keys())/col) 
    for idx,k in enumerate(db.keys()):
        plt.subplot(rows,col,idx)
        x,y = zip(*sorted(db[k].items(),key=lambda x: x[0]))
        plt.plot(list(x),[len(yi) for yi in y],label=truncate(k),c='black')
        plt.xticks([date(2012,3,1),date(2013,1,1),date(2013,11,1)],["03/2012","01/2013","11/2013"])
        plt.legend(loc=2,prop={'size':8})
    plt.tight_layout()
    plt.savefig('output_freq.png',orientation='landscape')
    return plt

def plot_key_mag(cache,key,limit=1000000000):
    db = {}
    col = 2 
    cache = list(cache)
    db = cache_to_dict(cache,key,limit)
    week = lambda x: trunc(x.fecha,'week')
    db = {k:cache_to_dict(db[k],week,limit) for k in db.keys()}
    plt.figure(figsize=(11,7))
    rows = round(len(db.keys())/col) 
    for idx,k in enumerate(db.keys()):
        plt.subplot(rows,col,idx)
        x,y = zip(*sorted(db[k].items(),key=lambda x: x[0]))
        plt.plot(list(x),[sum([c.precio for c in yi]) for yi in y],label=truncate(k),c='black')
        plt.xticks([date(2012,3,1),date(2013,1,1),date(2013,11,1)],["03/2012","01/2013","11/2013"])
        plt.legend(loc=2,prop={'size':8})
    plt.tight_layout()
    plt.savefig('output_mag.png',orientation='landscape')
    return plt

def truncate(data):
    return str(data[:20] + '..') if len(data) > 20 else data

def pie(cache,key,limit=1000000000):
    cache = list(cache)
    db = cache_to_dict(cache,key,limit)
    plt.figure(figsize=(11,7))
    plt.subplot(111)
    db = cache_to_dict(cache,key,limit)
    db = {k:sum([c.precio for c in db[k]]) for k in db.keys()}
    colormap,legends = colormap_for_key(db.keys())
#    plt.suptitle('CSS vs MINSA (compras entre $0 - \$%i)' % limit, fontdict=font)
    plt.pie(list(db.values()),labels=[locale.currency(v, grouping=True ) for v in db.values()],autopct='%1.1f%%',startangle=90,colors=colormap)
    legend,name = zip(*legends)
    plt.legend(legend, name, loc=2, prop={'size':8})
    plt.savefig('output_pie.png',orientation='landscape', bbox_inches=0,dpi=200)
    plt.tight_layout()
    return plt

def scatter(cache,key,limit=1000000000):
    cache = list(cache)
    db = cache_to_dict(cache,key,limit)
    plt.figure(figsize=(11,7))
    plt.subplot(111)
    price,time,color = cache_to_list(cache,key,limit)
    colormap,legends = colormap_for_key(color)
    plt.scatter(list(time),list(price),c=colormap,alpha=0.8,edgecolors='None')
    if limit > 10000: 
        plt.yscale('log', style='plain')
        plt.yticks(list([10**i for i in range(0,10)]))
    legend,name = zip(*legends)
    plt.legend(legend, name, loc=2, prop={'size':8})
    plt.savefig('output_scatter.png',orientation='landscape')
    plt.tight_layout()
    return plt

def cache_to_list(cache,key,limit):
    db = [(compra.precio,compra.fecha,key(compra)) for compra in cache if compra.precio < limit and key(compra) is not None]
    return list(zip(*db))

def cache_to_dict(cache,key,limit):
    db ={}
    for compra in filter(lambda x: x.precio < limit,cache):
        if key(compra) in db.keys():
            db[key(compra)].append(compra)
        else:
            db[key(compra)] = [compra]
    return db 

def colormap_for_key(key):
    key = list(key)
    keys = list({k for k in key}) #unique keys
    top_10 = sorted(keys,key=lambda x: key.count(x), reverse=True)
    if len(keys) > 10:
        top_10 = top_10[0:10]
    norm = mplcolor.Normalize(vmin=0, vmax=len(keys))
    m = cm.ScalarMappable(norm=norm, cmap=cm.Set1)
    if len(key) == 0:
        return []
    elif isinstance(key[0],date):
        return [m.to_rgba(d) for d in key]
    else:
        return ([m.to_rgba(keys.index(k)) for k in key],[legend_symbol_for_key(k,m.to_rgba(keys.index(k))) for k in top_10])

def legend_symbol_for_key(name,color):
    return (Circle((0, 0), 2, color=color),name)

def plot_precio_fecha_log(cache):
    cache = list(cache)
    plt.figure(figsize=(20, 8))
    plt.subplot(111)
    db = [(compra.precio,compra.fecha) for compra in cache]
    price,time = list(zip(*db))
    plt.scatter(list(time),list(price),c=[d.isocalendar()[1] for d in time],alpha=0.7,cmap=cm.Paired)
    average_max = db_worker.mode_price()[0]

    print(average_max)
    plt.axhline(y=average_max)
    return plt

def plot_precio_fecha(cache,limit=100000000):
    cache = list(cache)
    plt.figure(figsize=(20, 8))
    plt.subplot(111)
    db = [(compra.precio,compra.fecha) for compra in cache if compra.precio >= limit and compra.fecha is not None]
    price,time = list(zip(*db))
    plt.scatter(list(time),list(price),c=[d.month for d in time],alpha=0.7,cmap=cm.Paired)
    average_max = db_worker.mode_price()[0]
    plt.axhline(y=average_max)
    plt.text(date(2012,5,20), average_max, '$%i USD' % average_max, fontdict=font)
    return plt

def plot_css_mins(cache):
    css = []
    minsa = []
    t_minsa = []
    t_css = []
    print('got compras')
    for compra in cache:
        if compra.entidad == "MINISTERIO DE SALUD":
            minsa.append(compra.precio)
            t_minsa.append(compra.fecha)
        else:
            css.append(compra.precio)
            t_css.append(compra.fecha)
    plt.plot(t_css,css,'ro',t_minsa,minsa,'bs')
    plt.yscale('log')
    plt.show()

#cache = db_worker.history_price()
#cache = db_worker.query_frequency()

#cache = db_worker.query_all().all()
cache = db_worker.query_css_minsa().all()

#cache = filter(lambda x: 'ministerio' in x.entidad.lower(),cache)
print('got cache')
l = lambda x: x.entidad
#p = scatter(cache,l,1000)
#p = plot_key_freq(cache,l,3000)
#p = plot_key_mag(cache,l,3000)
p = pie(cache,l,3000)
#p.show()
#plt.ylabel('Price in USD', fontdict=font)
#p.savefig('all_l.png',orientation='landscape', bbox_inches=0,dpi=200)

#cache = filter(lambda x: x[1] > 100000,hospitales.all())
#hospitales,precios = zip(*cache)
#y_pos = np.arange(len(list(hospitales)))
#rc('ytick', labelsize=10) 
#plt.barh(y_pos, precios)
#plt.yticks(y_pos, hospitales)
#plt.show()
#plot_hospitales_precio(hospitales.all())
