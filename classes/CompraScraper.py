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
  def __init__(self, queue, session, connection):
    threading.Thread.__init__(self)
    self.compra_urls = queue
    self.logger = logging.getLogger('CompraScraper')
    self.logger = logging.getLogger('CompraScraper')
    self.connection = connection 
    self.session = session
    self.strainer = SoupStrainer('body')

  def run(self):
    while True:
      try:
        compra = self.compra_urls.get_nowait()
        self.eat_compra(compra)
        self.compra_urls.task_done()
      except Empty:
        self.logger.debug('worker dying %s', str(self))
        return
      except timeout:
        self.logger.debug('HTTP timeout from %s', str(self))
        continue

  def eat_compra(self,compra):
    url_path = "/AmbientePublico/" + compra.url #append path
    compra.html = self.get_compra_html(url_path)
    compra.visited = True
    self.session.merge(compra)
    self.session.commit()

  def get_compra_html(self,url):
    try:
        response = self.connection.request("GET", url)
        data = response.data
    except Exception as e:
        self.logger.debug('%s from %s',str(e) ,str(self))
    return unicode(BeautifulSoup(data, "html.parser", parse_only=self.strainer))
