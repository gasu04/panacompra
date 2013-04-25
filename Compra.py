class Compra():
  def __init__(self,url,category,html,data):
    self.url = url
    self.category = category
    self.html = html
    self.data = data

  def __str__(self):
    return str(self.data)

  def to_json(self):
    return {'url': self.url, 'category': self.category, 'data': self.data}
