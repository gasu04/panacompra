import re
from sqlalchemy import func
import logging
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime 
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker,undefer
from sqlalchemy import create_engine
from classes.Compra import Compra,Base
from multiprocessing import Pool,cpu_count,Lock
from modules import parser
from math import ceil
import itertools
import os

logger = logging.getLogger('DB')
CHUNK_SIZE=800

db_url = os.environ['panacompra_db']
db_url = "postgres://tcixoyjoepgpyi:BNLpWudAaZKshSptz3bDXx0CuK@ec2-54-221-204-17.compute-1.amazonaws.com:5432/d2trc2b2csosqf"
engine = create_engine(db_url, convert_unicode=True)
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)
session = session_maker()

def query_chunks(q, n):
  """ Yield successive n-sized chunks from query object."""
  for i in range(0, q.count(), n):
    yield list(itertools.islice(q, 0, n))

def chunks(l, n):
    """ return n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

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

def process_pending():
    count_query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True)
    query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).options(undefer('html')).limit(CHUNK_SIZE)
    pool = Pool(processes=cpu_count())
    while query.count() > 0:
        logger.info("%i compras pending", count_query.count())
        results = process_query(query,pool)
        merge_query(query,results)
    logger.info("compras added to db")

def merge_result(results):
    for compra in results:
        session.merge(compra)
        session.commit()

def process_query(query,pool):
    cache = query.all()
    results = pool.imap_unordered(process_compra, cache, int(ceil(len(cache)/cpu_count())))
    return results

def reparse():
    logger.info("Setting parsed to FALSE and parsing again")
    session.query(Compra).update({'parsed':False})
    session.commit()
    process_pending()

def query_not_visited():
    return session.query(Compra).filter(Compra.visited == False).limit(CHUNK_SIZE)

def count_not_visited():
    return session.query(Compra).filter(Compra.visited == False).count()

def reset_visited():
    session.query(Compra.Compra).update({'visited':False})
    session.commit()

def process_compras_queue(compras_queue,urls):
    while compras_queue.qsize() > 0:
        compra = compras_queue.get()
        compras_queue.task_done()
        if compra.url not in urls: 
            compra = process_compra(compra)
            session.add(compra) 
            urls.add(compra.url)
    session.commit()

def get_all_urls():
    try:
        urls = list(zip(*session.query(Compra.url).all()))[0]
        return {item.lower() for item in urls}
    except:
        return set()

def merge_query(query,result):
    query.merge_result(result)
    session.commit()

def query_css_minsa():
    return session.query(Compra).filter(Compra.category_id == 95).filter(Compra.parsed == True).options(undefer('entidad'),undefer('precio'),undefer('fecha'))

def hospitales():
    return session.query(Compra.unidad, func.sum(Compra.precio)).filter(Compra.category_id == 95).group_by(Compra.unidad)
