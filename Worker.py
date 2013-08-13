import logging
import threading
import httplib, urllib
from socket import timeout
from time import sleep
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
    self.logger = logging.getLogger('Worker')
    self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=60)

  def run(self):
    while True:
      try:
        url,category = self.compra_urls.get_nowait()
        self.eat_compra(url,category)
        self.compra_urls.task_done()
      except Empty:
        self.logger.debug('url queue is empty from %s', str(self))
        if any([scraper.is_alive() for scraper in self.scrapers]):
          sleep(15)
          continue
        else:
          self.connection.close()
          self.logger.info('worker dying %s', str(self))
          return
      except timeout:
        self.connection.close()
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=60)
        self.compra_urls.task_done()
        self.logger.info('HTTP timeout from %s', str(self))
        continue


  def eat_compra(self,url,category):
    url = "/AmbientePublico/" + url #append path
    html = self.get_compra_html(url)
    self.compras.put([html,url,category])

  def get_compra_html(self,url):
    self.connection.request("GET", url)
    response = self.connection.getresponse()
    data = response.read()
    return data

