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
  'descripcion': re.compile("(?:Descripcion\">)([^<]*)"),
  'fecha': re.compile("(?:Fecha de Public.*?>.*?>)([^<]*)"), 
  'acto': re.compile("(?:ero de Acto:</td><td class:\"formEjemplos\">)([^<]*)"),
  'entidad': re.compile("(?:Entidad:</td><td class:\"formEjemplos\">)([^<]*)"),
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
  no_quotes_or_newlines = no_quotes_or_newlines.decode('latin-1')
  return re.sub(' +',' ', no_quotes_or_newlines) #no repeated spaces

def parse_compra_html(html):
  data = {}
  for name,regex in regexes.iteritems():
    try:
      val = regex.findall(html)[0]
    except IndexError:
      logger.debug("%s not found",name)
      val = 'empty'
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
