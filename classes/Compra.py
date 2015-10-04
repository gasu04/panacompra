from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, Sequence, Boolean, Numeric, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm import deferred
from sqlalchemy.types import Unicode, UnicodeText
from datetime import datetime

Base = declarative_base()
class Compra(Base):
  __tablename__ = 'compras'

  id = Column(Integer, primary_key=True)
  acto = Column(Unicode(200), unique=True)
  url = Column(Unicode(200), unique=True)
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
  fecha = Column(DateTime)
  adquisiciones = relationship("Adquisicion")
  proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
  entidad_id = Column(Integer, ForeignKey('entidades.id'))
  htmls = relationship("CompraHtml")

  created_at = Column(Date, default=datetime.now())
  updated_at = Column(Date, default=datetime.now(), onupdate=datetime.now())


  def __init__(self,kwargs):
    self.visited = False
    self.parsed = False
    for k in  kwargs.keys():
        self.__setattr__(k, kwargs[k])


  def __hash__(self):
    return hash(self.url)

  def __eq__(self, other):
    return self.acto == other.acto

  def __getitem__(self,key):
    return getattr(self, key)

  def __str__(self):
    return "Compra(%s)" % (self.acto)

class Proveedor(Base):
  __tablename__ = 'proveedores'

  id = Column(Integer, primary_key=True)
  nombre = Column(Unicode, unique=True)
  compras = relationship(Compra)
  created_at = Column(Date, default=datetime.now())
  updated_at = Column(Date, default=datetime.now, onupdate=datetime.now())

  def __init__(self,nombre):
    self.nombre = nombre

class Entidad(Base):
  __tablename__ = 'entidades'

  id = Column(Integer, primary_key=True)
  nombre = Column(Unicode, unique=True)
  compras = relationship(Compra)
  created_at = Column(Date, default=datetime.now())
  updated_at = Column(Date, default=datetime.now(), onupdate=datetime.now())

  def __init__(self,nombre):
    self.nombre = nombre

class Adquisicion(Base):
  __tablename__ = 'adquisiciones'

  id = Column(Integer, primary_key=True)
  codigo = Column(Numeric)
  clasificacion = Column(Unicode)
  cantidad = Column(Numeric)
  unidad = Column(Unicode)
  descripcion= Column(Unicode)
  ses = Column(Unicode)
  categoria_1 = Column(Unicode)
  categoria_2 = Column(Unicode)
  categoria_3 = Column(Unicode)
  compra_id = Column(Integer, ForeignKey('compras.id'))
  created_at = Column(Date, default=datetime.now())
  updated_at = Column(Date, default=datetime.now, onupdate=datetime.now())

  def __init__(self, kwargs):
    for k in  kwargs.keys():
        self.__setattr__(k, kwargs[k])

class CompraHtml(Base):
  __tablename__ = 'compra_htmls'

  id = Column(Integer, primary_key=True)
  html = deferred(Column(UnicodeText))
  compra_id = Column(Integer, ForeignKey('compras.id'))
  created_at = Column(Date, default=datetime.now)
  updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)

  def __init__(self, kwargs):
    for k in  kwargs.keys():
        self.__setattr__(k, kwargs[k])

