import logging
import threading
import httplib, urllib
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

  def run(self):
    while True:
      try:
        url,category = self.compra_urls.get_nowait()
        self.eat_compra(url,category)
        self.compra_urls.task_done()
      except Empty:
        self.logger.debug('url queue is empty from %s', str(self))
        if any([scraper.is_alive() for scraper in self.scrapers]):
          sleep(5)
          continue
        else:
          self.logger.debug('worker dying %s', str(self))
          return

  def eat_compra(self,url,category):
    url = "/AmbientePublico/" + url #append path
    html = self.get_compra_html(url)
    self.compras.put([html,url,category])

  def get_compra_html(self,url):
    connection = httplib.HTTPConnection("201.227.172.42", "80")
    connection.request("GET", url)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

