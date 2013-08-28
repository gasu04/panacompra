from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import *
from sqlalchemy.types import Unicode, UnicodeText

Base = declarative_base()

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
    return self.convert({'compra[url]':self.url, 'compra[category_id]':self.category, 'compra[entidad]':self.entidad, 'compra[proponente]':self.proponente, 'compra[description]':self.description, 'compra[precio]':self.precio, 'compra[fecha]':date, 'compra[acto]':self.acto })

  def to_dict(self):
    try:
      date = self.fecha.isoformat()
    except:
      date = None
    return self.convert({'url':self.url, 'category_id':self.category, 'entidad':self.entidad, 'proponente':self.proponente, 'description':self.description, 'precio':self.precio, 'fecha':date, 'acto':self.acto })

  def convert(self, obj):
    for key,val in obj.iteritems():
      if val != None and (key == 'entidad' or key == 'proponente' or key == 'description'):
        obj[key] = val.encode('latin-1', 'ignore')
    return obj

  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.url)

