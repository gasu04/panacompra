import re
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from sqlalchemy.orm import deferred
from sqlalchemy.types import Unicode, UnicodeText
from bs4 import BeautifulSoup,SoupStrainer
from datetime import datetime
from decimal import Decimal

Base = declarative_base()

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except:
    date= None
  return date

def parse_precio(precio):
  precio = re.sub(r'[^\d.]', '',precio) #remove non digits
  precio = re.sub(r'^.', '',precio) #remove leading period
  if not precio == "":
    precio = Decimal(precio)
  else:
    precio = Decimal(0) 
  return precio

def sanitize(string):
  no_quotes_or_newlines = string.replace('"', '').replace("'","").replace('\n',' ').replace('\r',' ').strip() 
  return re.sub(' +',' ', no_quotes_or_newlines) #no repeated spaces

def parse_and_sanitize(string,name):
  string = sanitize(string)
  if name == "fecha":
    string = parse_date(string)
  elif name == 'precio' or name == 'precio_cd':
    string = parse_precio(string)
  elif name == 'proponente':
    string = sanitize(string[:199])
  elif name == 'telefono_contacto':
    string = string[:14]
  return string

class Compra(Base):
  __tablename__ = 'compras'
  
  id = Column(Integer, Sequence('compras_id_seq'))
  url = Column(String(200), primary_key=True)
  html = deferred(Column(UnicodeText))
  visited = Column(Boolean)
  parsed = Column(Boolean)
  category_id = Column(Integer(3))
  compra_type = Column(Unicode(100))
  entidad = Column(Unicode(200))
  dependencia = Column(Unicode(200))
  nombre_contacto = Column(Unicode(40))
  telefono_contacto = Column(Unicode(15))
  objeto = Column(Unicode(200))
  modalidad = Column(Unicode(200))
  correo_contacto = Column(Unicode(200))
  unidad = Column(Unicode(200))
  provincia = Column(Unicode(50))
  precio = Column(Numeric(15,2))
  precio_cd = Column(Numeric(15,2))
  proponente = Column(Unicode(200),default=unicode('empty'))
  description = deferred(Column(UnicodeText))
  acto = Column(Unicode(200))
  fecha = Column(DateTime)
  created_at = Column(Date, default=datetime.now)
  updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)


  def __init__(self,url,category):
    self.url = url
    self.category_id = category
    self.html = None
    self.visited = False
    self.parsed = False

  def convert(self, obj):
    for key,val in obj.iteritems():
      if val != None and (key == 'entidad' or key == 'proponente' or key == 'description'):
        obj[key] = val.encode('latin-1', 'ignore')
    return obj

  def parse_html(self,methods):
    soup = BeautifulSoup(self.html,'html.parser',parse_only=SoupStrainer('tr'))
    for name,method in methods.iteritems():
      val = method(soup)
      setattr(self,name,val)
    self.parsed = True
    del self.html
    return self
  
  def __hash__(self):
    return hash(self.url)

  def __eq__(self, other):
    return self.url == other.url
    
  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.url)

