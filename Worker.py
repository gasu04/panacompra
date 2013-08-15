import logging
import threading
import httplib, urllib
from socket import timeout
from time import sleep
from Queue import Empty
import Compra
from sqlalchemy import create_engine
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker

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
    self.engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra', echo=False,convert_unicode=False)
    self.session_maker = sessionmaker(bind=self.engine)
    self.connection = False

  def open_connection(self):
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=10)
      except:
        self.logger.info('HTTP timeout in %s', str(self))
        continue

  def reset_connection(self):
    self.connection.close()
    self.connection = False
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=15)
      except:
        self.logger.info('HTTP timeout in %s', str(self))
        continue

  def run(self):
    session = self.session_maker()
    Compra.Base.metadata.create_all(self.engine)
    self.open_connection()
    while True:
      try:
        url,category = self.compra_urls.get_nowait()
        if not session.query(exists().where(Compra.Compra.url==("/AmbientePublico/" + url))).scalar():
          self.eat_compra(url,category)
        self.compra_urls.task_done()
      except Empty:
        self.logger.debug('url queue is empty from %s', str(self))
        if any([scraper.is_alive() for scraper in self.scrapers]):
          sleep(15)
          continue
        else:
          self.connection.close()
          session.close()
          self.logger.info('worker dying %s', str(self))
          return
      except timeout:
        self.reset_connection()
        self.logger.info('HTTP timeout from %s', str(self))
        continue

  def eat_compra(self,url,category):
    url = "/AmbientePublico/" + url #append path
    html = self.get_compra_html(url)
    self.compras.put([html,url,category])

  def get_compra_html(self,url):
    success = False
    while not success:
      try:
        self.connection.request("GET", url)
        response = self.connection.getresponse()
        data = response.read()
      except Exception as e:
        sleep(1)
        self.logger.info('RESPONSE timeout from %s', str(self))
        self.reset_connection()
        sleep(1)
        continue
    return data
