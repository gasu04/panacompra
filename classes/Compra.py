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
  description = deferred(Column(UnicodeText))
  visited = Column(Boolean)
  parsed = Column(Boolean)
  category_id = Column(Integer)
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
  proponente = Column(Unicode(200))
  acto = Column(Unicode(200), unique=True)
  fecha = Column(DateTime)
  created_at = Column(Date, default=datetime.now)
  updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)

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

