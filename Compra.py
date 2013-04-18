class Compra():
  def __init__(self,url,html,data):
    self.url = url
    self.html = html
    self.data = data

  def __str__(self):
    return str(self.data)

  def to_json(self):
    return {'url': self.url, 'data': self.data}
