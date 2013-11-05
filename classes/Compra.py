from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, Sequence, Boolean, Numeric, DateTime
from sqlalchemy.orm import deferred
from sqlalchemy.types import Unicode, UnicodeText
from datetime import datetime

Base = declarative_base()
class Compra(Base):
  __tablename__ = 'compras'
  
  id = Column(Integer, Sequence('compras_id_seq'), primary_key=True)
  url = Column(Unicode(200), unique=True)
  html = deferred(Column(UnicodeText))
  visited = deferred(Column(Boolean))
  parsed = deferred(Column(Boolean))
  category_id = deferred(Column(Integer(3)))
  compra_type = deferred(Column(Unicode(100)))
  entidad = deferred(Column(Unicode(200)))
  dependencia = deferred(Column(Unicode(200)))
  nombre_contacto = deferred(Column(Unicode(40)))
  telefono_contacto = deferred(Column(Unicode(15)))
  objeto = deferred(Column(Unicode(200)))
  modalidad = deferred(Column(Unicode(200)))
  correo_contacto = deferred(Column(Unicode(200)))
  unidad = deferred(Column(Unicode(200)))
  provincia = deferred(Column(Unicode(50)))
  precio = deferred(Column(Numeric(15,2)))
  precio_cd = deferred(Column(Numeric(15,2)))
  proponente = deferred(Column(Unicode(200)))
  description = deferred(Column(UnicodeText))
  acto = deferred(Column(Unicode(200), unique=True))
  fecha = deferred(Column(DateTime))
  created_at = deferred(Column(Date, default=datetime.now))
  updated_at = deferred(Column(Date, default=datetime.now, onupdate=datetime.now))

  def __init__(self,url,category):
    self.url = str(url)
    self.category_id = category
    self.html = None
    self.visited = False
    self.parsed = False

  def __hash__(self):
    return hash(self.url)

  def __eq__(self, other):
    return self.url == other.url
    
  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.acto)

