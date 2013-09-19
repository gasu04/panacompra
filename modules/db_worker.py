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
CHUNK_SIZE=1000

def chunks(q, n):
  """ Yield successive n-sized chunks from query object."""
  for i in xrange(0, q.count(), n):
    yield q[i:i+n]

def process_compras_chunk(chunk):
  regexes = {
    'precio': re.compile("(?:Precio.*?>.*?>[^0-9]*)([0-9,]*\.[0-9][0-9]*)"),
    'description': re.compile('(?:Descripci[^n]n:</td><td class="formEjemplos">)([^<]*)'),
    'compra_type': re.compile('(?:Procedimiento:</td><td class="formEjemplos">)([^<]*)'),
    'dependencia': re.compile('(?:Dependencia:</td><td class="formEjemplos">)([^<]*)'),
    'unidad': re.compile('(?:Unidad de Compra:</td><td class="formEjemplos">)([^<]*)'),
    'objeto': re.compile('(?:Contractual:</td><td class="formEjemplos">)([^<]*)'),
    'modalidad': re.compile('(?:Modalidad de adjudicaci.n:</td><td class="formEjemplos">)([^<]*)'),
    'provincia': re.compile('(?:Provincia de Entrega:</td><td class="formEjemplos">)([^<]*)'),
    'correo_contacto': re.compile('(?:formTextos[^w]*width[^C]*Correo Electr.nico:</td><td class="formEjemplos">)([^<]*)'),
    'nombre_contacto': re.compile('(?:Datos de Contacto[^N]*Nombre:</td><td class="formEjemplos">)([^<]*)'),
    'telefono_contacto': re.compile('(?:Tel[^:]*:</td><td class="formEjemplos">)([^<]*)'),
    'fecha': re.compile("(?:Fecha de Public.*?>.*?>)([^<]*)"), 
    'acto': re.compile("(?:de Acto.*?>.*?>)([^<]*)"),
    'entidad': re.compile("(?:Entidad.................formEjemplos..)([^<]*)"),
    'proponente': re.compile("(?:Proponente.*\n.*\n.*?Ejemplos\">)([^<]*)",re.MULTILINE)
  }
  return [compra.parse_html(regexes) for compra in chunk]

def process_pending(engine):
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  logger.info("%i compras pending", session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).count())
  query = chunks(session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).yield_per(CHUNK_SIZE),CHUNK_SIZE)
  pool = Pool(processes=cpu_count())
  batch_size = cpu_count()
  done = False
  while not done:
    try:
      batch = []
      for i in range(batch_size):
        batch.append(query.next())
    except StopIteration:
      done = True
    finally:
      for chunk in pool.imap_unordered(process_compras_chunk, batch):
        for compra in chunk:
          session.merge(compra)
    session.commit()
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
