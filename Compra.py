from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *

Base = declarative_base()

class Compra(Base):
  __tablename__ = 'compras'
  
  id = Column(Integer, Sequence('compra_id_seq'), primary_key=True)
  url = Column(String(200))
  category = Column(String(50))
  entidad = Column(String(250))
  precio = Column(Float(50))
  proponente = Column(String(250))

  def __init__(self,url,category,html,data):
    self.url = url
    self.category = category
    self.html = html
    self.data = data
    self.categories = {50: "Alimentos, Bebidas y Tabaco",15:"Combustibles, Aditivos para combustibles, Lubricantes y Materiales Anticorrosivos",31:'Componentes y Suministros de Fabricacion', 30:'Componentes y Suministros de Fabricacion, Estructuras, Obras y Construcciones',25:'Componentes y Suministros Electronicos',35:'Vehiculos Comerciales, Militares y Particulares, Accesorios y Componentes'}
    self.precio = data['precio']
    self.entidad = data['entidad']
    self.proponente = data['proponente']

  def translate_category(self,category_number):
    if category_number in self.categories:
      return self.categories[category_number]
    return category_number

  def __str__(self):
    return str(self.data)

  def to_json(self):
    return {'url': self.url, 'category': self.translate_category(self.category), 'data': self.data}

  def to_insert(self):
    return [self.data['entidad'],self.translate_category(self.category),self.data['proponente'],self.data['precio'],self.data['fecha'],self.data['acto'],self.data['descripcion']]

  def __repr__(self):
    return "<Compra('%s', '%s', '%s')>" % (self.entidad, self.precio, self.proponente)
