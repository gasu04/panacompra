import threading
import httplib, urllib
import re
from Compra import Compra
from time import sleep
from bs4 import BeautifulSoup
from Queue import Empty

class WorkThread(threading.Thread):
  """
  Scrapes pages using urls from compra_url Queue
  Parses html, creates Compra objects , adds them to compras Queue

  """
  def __init__(self, queue, out_queue, scrapers):
    threading.Thread.__init__(self)
    self.compra_urls = queue
    self.compras = out_queue
    self.scrapers = scrapers
    self.precio_regex = re.compile("(?:Precio.*?>.*?>[^0-9]*)([0-9]*\.[0-9][0-9]*)") 
    self.acto_regex = re.compile("(?:ero de Acto:</td><td class=\"formEjemplos\">)([^<]*)")
    self.entidad_regex = re.compile("(?:Entidad:</td><td class=\"formEjemplos\">)([^<]*)") 
    self.proponente_regex = re.compile("(?:Proponente.*\n.*\n.*?Ejemplos\">)([^<]*)",re.MULTILINE)

  def run(self):
    while True:
      try:
        url = self.compra_urls.get_nowait()
        self.compra_urls.task_done()
        self.eat_compra(url)
      except Empty:
        if any([scraper.is_alive() for scraper in self.scrapers]):
          sleep(1)
          continue
        else:
          print 'worker dying'
          return

  def eat_compra(self,url):
    url = "/AmbientePublico/" + url #append path
    html = self.get_compra_html(url)
    self.compras.put(Compra(url,html,self.parse_compra_html(html))) #create and store Compra object

  def parse_compra_html(self,html):
    try:
      acto = self.acto_regex.findall(html)[0].encode('ascii', 'ignore')
    except:
      acto = "empty"
    try:
      entidad = self.entidad_regex.findall(html)[0].encode('ascii', 'ignore')
    except:
      entidad = "empty"
    try:
      precio = self.precio_regex.findall(html)[0].encode('ascii', 'ignore')
    except:
      precio = "empty"
    try:
      proponente = self.proponente_regex.findall(html)[0].encode('ascii', 'ignore')
    except:
      proponente = "empty"
    return { 'entidad' : entidad, 'acto': acto, 'precio' : precio, 'proponente' : proponente}

  def get_compra_html(self,url):
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    connection.request("GET", url)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

