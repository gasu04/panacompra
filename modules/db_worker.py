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

logger = logging.getLogger('db_worker')
CHUNK_SIZE=800

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
    pool = Pool(processes=cpu_count())
    while query.count() > 0:
        logger.info("%i compras pending", count_query.count())
        results = process_query(query,pool)
        query.merge_result(results)
        session.commit()
    logger.info("compras added to db")

def process_query(query,pool):
    cache = query.all()
    results = pool.imap_unordered(process_compra, cache, int(ceil(len(cache)/cpu_count())))
    return results

def reparse():
    session = session_maker()
    logger.info("Setting parsed to FALSE and parsing again")
    session.query(Compra).update({'parsed':False})
    session.commit()
    process_pending()

def query_not_visited():
    session = session_maker()
    return session.query(Compra).filter(Compra.visited == False).limit(CHUNK_SIZE)

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

def query_css_minsa():
    session = session_maker()
    return session.query(Compra).filter(Compra.category_id == 95).filter(Compra.parsed == True).options(undefer('entidad'),undefer('precio'),undefer('fecha'))

def hospitales():
    session = session_maker()
    return session.query(Compra.unidad, func.sum(Compra.precio)).filter(Compra.category_id == 95).group_by(Compra.unidad)
