from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import *
from sqlalchemy.types import Unicode, UnicodeText

Base = declarative_base()

class Compra(Base):
  __tablename__ = 'compras'
  
  id = Column(Integer, Sequence('compra_id_seq'), primary_key=True)
  url = Column(String(200))
  html = Column(UnicodeText(65000))
  visited = Column(Boolean)
  parsed = Column(Boolean)
  category = Column(Integer(3))
  entidad = Column(Unicode(200))
  precio = Column(Float(50))
  proponente = Column(Unicode(200))
  description = Column(Unicode(500))
  acto = Column(Unicode(200))
  fecha = Column(DateTime)

  def __init__(self,url,category):
    self.url = url
    self.category = category
    self.html = None
    self.visited = False
    self.parsed = False

  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.url)

