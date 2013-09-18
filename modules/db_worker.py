import re
import logging
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime 
from sqlalchemy.sql import exists
from classes.Compra import Compra
from multiprocessing import pool,cpu_count

logger = logging.getLogger('DB')

def chunks(q, n):
    """ Yield successive n-sized chunks from query object."""
    for i in xrange(0, q.count(), n):
        yield l[i:i+n]

def process_compras_chunk(lock, query, session)
  lock.acquire()
  chunk = query.next()
  lock.release()
  for compra in chunk:
    compra.parse_html()
    session.merge(compra)
  session.commit()

def process_pending(session_maker):
  logger.info("%i compras pending", session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).count())
  session = session_maker()
  query = session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).yield_per(500)
  pool = Pool(processes=cpu_count())
  lock = Lock()
  pool.apply_async(procsess_compras_chunk, (lock, query, session_maker()))
  logger.info("compras added to db")
  session.close()

def reparse(session_maker):
  session = session_maker()
  logger.info("Setting parsed to FALSE and parsing again")
  session.query(Compra).update({'parsed':False})
  session.commit()
  process_pending(session)
