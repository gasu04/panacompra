import re
import logging
from datetime import datetime
from time import sleep
from time import strptime
from time import strftime 
from sqlalchemy.sql import exists
from classes.Compra import Compra

logger = logging.getLogger('DB')
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
  'fecha': re.compile("(?:Fecha de Public.*?>.*?>)([^<]*)"), 
  'acto': re.compile("(?:de Acto...............................)([^<]*)"),
  'entidad': re.compile("(?:Entidad.................formEjemplos..)([^<]*)"),
  'proponente': re.compile("(?:Proponente.*\n.*\n.*?Ejemplos\">)([^<]*)",re.MULTILINE)
}

def process_pending(session):
  count = 0 
  while session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).count() > 0:
    for compra in session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).limit(100):
      try:
        data = parse_compra_html(compra.html)
        update_compra(compra,data)
        session.merge(compra)
        count += 1
      except Exception as e:
        print e
        continue
  session.commit()
  logger.info("%i compras added to db", count)
  session.close()

def reparse(session):
  logger.info("Setting parsed to FALSE and parsing again")
  count = 0 
  session.query(Compra).update({'parsed':False})
  while session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).count() > 0:
    for compra in session.query(Compra).filter(Compra.parsed == False).filter(Compra.visited == True).limit(100):
      try:
        data = parse_compra_html(compra.html)
        update_compra(compra,data)
        session.merge(compra)
        count += 1
      except Exception as e:
        print e
        continue
  session.commit()
  logger.info("%i compras added to db", count)
  session.close()

def update_compra(compra, data):
  for key,val in data.iteritems():
    setattr(compra,key,val)
  compra.parsed = True

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except:
    logger.debug('could not parse date')
    date= None
  return date

def parse_precio(precio):
  precio = re.sub(r'[^\d.]', '',precio) #remove non digits
  if not precio == "":
    precio = float(precio)
  else:
    precio = 0.00
  return precio

def sanitize(string):
  no_quotes_or_newlines = string.replace('"', '').replace("'","").replace('\n',' ').replace('\r',' ').strip() 
  return re.sub(' +',' ', no_quotes_or_newlines) #no repeated spaces

def parse_compra_html(html):
  data = {}
  for name,regex in regexes.iteritems():
    try:
      val = regex.findall(html)[0]
    except IndexError:
      logger.debug("%s not found",name)
      val = unicode('empty')
    if name == "fecha":
      val = parse_date(val)
    elif name == 'precio':
      val = parse_precio(val)
    elif name == 'proponente':
      val = sanitize(val[:199])
    else:
      val = sanitize(val)
    data[name] = val
  return data
