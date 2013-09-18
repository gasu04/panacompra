import re
import logging
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime 
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker
from classes.Compra import Compra
from multiprocessing import Pool,cpu_count,Lock

logger = logging.getLogger('DB')

def chunks(q, n):
  """ Yield successive n-sized chunks from query object."""
  for i in xrange(0, q.count(), n):
    yield q[i:i+n]

def process_compras_chunk(chunk):
  return [compra.parse_html() for compra in chunk]

def process_pending(engine):
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  logger.info("%i compras pending", session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).count())
  query = chunks(session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).yield_per(500),500)
  pool = Pool(processes=cpu_count())
  batch_size = cpu_count()
  while True:
    try:
      for chunk in pool.imap(process_compras_chunk, [query.next() for i in range(cpu_count())]):
        for compra in chunk:
          session.merge(compra)
      session.commit()
    except StopIteration:
      session.commit()
      if batch_size == 0: 
        break
      else:
        batch_size = batch_size - 1
        continue
  logger.info("compras added to db")
  session.close()

def reparse(engine):
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  logger.info("Setting parsed to FALSE and parsing again")
  session.query(Compra).update({'parsed':False})
  session.commit()
  session.close()
  process_pending(engine)
