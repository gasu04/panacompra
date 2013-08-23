from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *

Base = declarative_base()

class Url(Base):
  __tablename__ = 'urls'
  
  id = Column(Integer, Sequence('compra_id_seq'), primary_key=True)
  url = Column(String(200))
  html = Column(LargeBinary(80000))
  category = Column(Integer(3))
  visited = Column(Boolean)
  parsed = Column(Boolean)
  status  = Column(Boolean)

  def __init__(self,url,category):
    self.url = url
    self.category = category
    self.visited = False
    self.parsed = False

  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Url(%s)" % (self.url)