class Compra():
  def __init__(self,url,category,html,data):
    self.url = url
    self.category = category
    self.html = html
    self.data = data
    self.categories = {50: "Alimentos, Bebidas y Tabaco",15:"Combustibles, Aditivos para combustibles, Lubricantes y Materiales Anticorrosivos",31:'Componentes y Suministros de Fabricacion', 30:'Componentes y Suministros de Fabricacion, Estructuras, Obras y Construcciones',25:'Componentes y Suministros Electronicos',35:'Vehiculos Comerciales, Militares y Particulares, Accesorios y Componentes'}

  def translate_category(self,category_number):
    if category_number in self.categories:
      return self.categories[category_number]
    return category_number

  def __str__(self):
    return str(self.data)


  def to_json(self):
    return {'url': self.url, 'category': self.translate_category(self.category), 'data': self.data}
