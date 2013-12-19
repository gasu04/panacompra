import re
from sqlalchemy import or_
from sqlalchemy import func
import logging
from scipy import stats
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime 
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker,undefer
from sqlalchemy import create_engine
from sqlalchemy import Date, cast
from datetime import date
from classes.Compra import Compra,Base
from multiprocessing import Pool,cpu_count,Lock
from modules import parser
from math import ceil
import itertools
import os

logger = logging.getLogger('db_worker')
CHUNK_SIZE=3800

db_url = os.environ['panacompra_db']
logger.info('loading %s', db_url)
engine = create_engine(db_url, convert_unicode=True, echo=False)
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)

def query_chunks(q, n):
  """ Yield successive n-sized chunks from query object."""
  for i in range(0, q.count(), n):
    yield list(itertools.islice(q, 0, n))

def chunks(l, n):
    """ return n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

def process_pending():
    session = session_maker()
    count_query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True)
    query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).options(undefer('html')).limit(CHUNK_SIZE)
    pool = Pool(processes=1)
    while query.count() > 0:
        logger.info("%i compras pending", count_query.count())
        results = process_query(query,pool)
        query.merge_result(results)
        session.commit()
    logger.info("compras added to db")

def process_compra(compra):
  modules = {
    'precio': parser.extract_precio,
    'description': parser.extract_description,
    'compra_type': parser.extract_compra_type,
    'dependencia': parser.extract_dependencia,
    'unidad': parser.extract_unidad,
    'objeto': parser.extract_objeto,
    'modalidad': parser.extract_modalidad,
    'provincia': parser.extract_provincia,
    'correo_contacto': parser.extract_correo_contacto,
    'nombre_contacto': parser.extract_nombre_contacto,
    'telefono_contacto': parser.extract_telefono_contacto,
    'fecha': parser.extract_fecha,
    'acto': parser.extract_acto,
    'entidad': parser.extract_entidad,
    'proponente': parser.extract_proponente
  }
  compra = parser.parse_html(compra,modules)
  return compra

def process_query(query,pool):
    cache = query.all()
    results = pool.imap_unordered(process_compra, cache, int(ceil(len(cache)/1)))
    return results

def reparse():
    session = session_maker()
    logger.info("Setting parsed to FALSE and parsing again")
    session.query(Compra).update({'parsed':False})
    session.commit()
    process_pending()

def query_not_visited():
    session = session_maker()
    cache = list(session.query(Compra).filter(Compra.visited == False))
    session.close()
    return cache

def count_not_visited():
    session = session_maker()
    return session.query(Compra).filter(Compra.visited == False).count()

def reset_visited():
    session = session_maker()
    session.query(Compra.Compra).update({'visited':False})
    session.commit()

def create_compra(compra):
    session = session_maker()
    session.add(compra) 
    logger.info('got new compra %s', compra.acto)
    session.commit()

def get_all_urls():
    session = session_maker()
    try:
        urls = list(zip(*session.query(Compra.url).all()))[0]
        return {item.lower() for item in urls}
    except:
        return set()

def query_all():
    session = session_maker()
    return session.query(Compra).filter(Compra.parsed == True).filter(Compra.precio > 0).filter(Compra.fecha != None)

def mode_price():
    session = session_maker()
    maxes = session.query(func.max(Compra.precio)).group_by(cast(Compra.fecha,Date)).all()
    return stats.mode(list(filter(None,[m[0] for m in maxes])))

def history_price():
    session = session_maker()
    history = session.query(Compra.entidad,func.sum(Compra.precio),func.date_trunc('month', Compra.fecha)).group_by(Compra.entidad,func.date_trunc('month',Compra.fecha)).order_by(func.date_trunc('month',Compra.fecha)).filter(Compra.entidad.startswith('MINISTERIO')).all()
    return history

def query_frequency():
    session = session_maker()
    return session.query(Compra.entidad,func.count(),func.date_trunc('week',Compra.fecha,)).filter(Compra.precio > 0).filter(Compra.fecha != None).group_by(Compra.entidad,func.date_trunc('week',Compra.fecha)).order_by(func.date_trunc('week',Compra.fecha)).filter(Compra.entidad.startswith('MINISTERIO')).all()


def query_css_minsa():
    session = session_maker()
    return session.query(Compra).filter(or_(Compra.entidad == 'CAJA DE SEGURO SOCIAL', Compra.entidad == 'MINISTERIO DE SALUD')).filter(Compra.parsed == True)

def hospitales():
    session = session_maker()
    return session.query(Compra.unidad, func.sum(Compra.precio)).filter(Compra.category_id == 95).group_by(Compra.unidad)
