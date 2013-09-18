import re
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import *
from sqlalchemy.types import Unicode, UnicodeText

Base = declarative_base()

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

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except:
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

def parse_and_sanitize(string,name):
  string = sanitize(string)
  if name == "fecha":
    string = parse_date(string)
  elif name == 'precio':
    string = parse_precio(string)
  elif name == 'proponente':
    string = sanitize(string[:199])
  elif name == 'telefono_contacto':
    string = string[:14]
  return string

class Compra(Base):
  __tablename__ = 'compras'
  
  id = Column(Integer, Sequence('compra_id_seq'), primary_key=True)
  url = Column(String(200))
  html = Column(UnicodeText)
  visited = Column(Boolean)
  parsed = Column(Boolean)
  category = Column(Integer(3))
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
  precio = Column(Float(50))
  proponente = Column(Unicode(200))
  description = Column(UnicodeText)
  acto = Column(Unicode(200))
  fecha = Column(DateTime)

  def __init__(self,url,category):
    self.url = url
    self.category = category
    self.html = None
    self.visited = False
    self.parsed = False

  def to_json(self):
    try:
      date = self.fecha.isoformat()
    except:
      date = None
    return self.convert({'compra[url]':self.url, 'compra[category_id]':self.category, 'compra[entidad]':self.entidad, 'compra[proponente]':self.proponente, 'compra[description]':self.description, 'compra[precio]':self.precio, 'compra[fecha]':date, 'compra[acto]':self.acto, 'compra[compra_type]':self.compra_type, 'compra[dependencia]': self.dependencia, 'compra[nombre_contacto]':self.nombre_contacto, 'compra[telefono_contacto]': self.telefono_contacto, 'compra[correo_contacto]': self.correo_contacto, 'compra[objeto]': self.objeto, 'compra[modalidad]': self.modalidad, 'compra[unidad]': self.unidad, 'compra[provincia]': self.provincia})

  def to_dict(self):
    try:
      date = self.fecha.isoformat()
    except:
      date = None
    return self.convert({'url':self.url, 'category_id':self.category, 'entidad':self.entidad, 'proponente':self.proponente, 'description':self.description, 'precio':self.precio, 'fecha':date, 'acto':self.acto, 'compra_type':self.compra_type, 'dependencia': self.dependencia, 'nombre_contacto':self.nombre_contacto, 'telefono_contacto': self.telefono_contacto, 'correo_contacto': self.correo_contacto, 'objeto': self.objeto, 'modalidad': self.modalidad, 'unidad': self.unidad, 'provincia': self.provincia })

  def convert(self, obj):
    for key,val in obj.iteritems():
      if val != None and (key == 'entidad' or key == 'proponente' or key == 'description'):
        obj[key] = val.encode('latin-1', 'ignore')
    return obj

  def parse_html(self):
    for name,regex in regexes.iteritems():
      try:
        val = regex.findall(self.html)[0]
      except IndexError:
        val = unicode('empty')
      setattr(self,name,parse_and_sanitize(val,name))
    self.parsed = True
    
  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.url)

