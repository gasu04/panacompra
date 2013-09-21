import logging
import threading
import httplib, urllib
from socket import timeout
from time import sleep
from Queue import Empty
from bs4 import BeautifulSoup, SoupStrainer

class CompraScraperThread(threading.Thread):
  """
  Scrapes pages using urls from compra_url Queue
  """
  def __init__(self, queue, session):
    threading.Thread.__init__(self)
    self.compra_urls = queue
    self.logger = logging.getLogger('CompraScraper')
    self.logger = logging.getLogger('CompraScraper')
    self.connection = False
    self.session = session
    self.strainer = SoupStrainer('body')

  def open_connection(self):
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=20)
      except:
        self.logger.debug('HTTP timeout in %s', str(self))
        continue

  def reset_connection(self):
    self.connection.close()
    self.connection = False
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=20)
      except:
        self.logger.debug('HTTP timeout in %s', str(self))
        continue

  def run(self):
    self.open_connection()
    while True:
      try:
        compra = self.compra_urls.get_nowait()
        self.eat_compra(compra)
        self.compra_urls.task_done()
      except Empty:
        self.connection.close()
        self.logger.info('worker dying %s', str(self))
        return
      except timeout:
        self.reset_connection()
        self.logger.debug('HTTP timeout from %s', str(self))
        continue

  def eat_compra(self,compra):
    url_path = "http:///AmbientePublico/" + compra.url #append path
    compra.html = self.get_compra_html(url_path)
    compra.visited = True
    self.session.merge(compra)
    self.session.commit()

  def get_compra_html(self,url):
    done = False
    while not done:
      try:
        self.connection.request("GET", url)
        response = self.connection.getresponse()
        data = response.read()
        done = True
      except Exception as e:
        self.logger.debug('%s from %s',str(e) ,str(self))
        self.reset_connection()
        continue
    return unicode(BeautifulSoup(data, "html.parser", parse_only=self.strainer))
