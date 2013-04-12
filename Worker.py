import threading
import httplib, urllib
from Compra import Compra
from time import sleep

class WorkThread(threading.Thread):
  def __init__(self, queue, out_queue, scrapers):
    threading.Thread.__init__(self)
    self.compra_urls = queue
    self.compras = out_queue
    self.scrapers = scrapers

  def run(self):
    while True:
      try:
        url = self.compra_urls.get_nowait()
        self.eat_compra(url)
        self.compra_urls.task_done()
      except:
        if any([scraper.is_alive() for scraper in self.scrapers]):
          sleep(1)
          continue
        else:
          return

  def eat_compra(self,url):
    html = self.get_compra_html(url)
    self.compras.put(Compra(url,html,self.parse_compra_html(html))) #create and store Compra object

  def parse_compra_html(self,html):
    return [1]

  def get_compra_html(self,url):
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    url = "/AmbientePublico/" + url #append path
    connection.request("GET", url)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

