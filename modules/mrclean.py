import re
import logging
from datetime import datetime

logger = logging.getLogger('mrclean')

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except:
    logger.debug('could not parse date')
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
