from bs4 import BeautifulSoup, SoupStrainer

import httplib, urllib
from random import shuffle
import re
import sys
import logging
import threading
import sys,os,signal
from Queue import Queue
from Scraper import ScrapeThread
from time import sleep
from Worker import WorkThread
from DBWorker import DBWorker
from modules import rails
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct
import Compra
import Url

class PanaCrawler():
  """
  Main Crawler class

  Scrapes Category Ids
  Spawns all threads ( WorkerThread, ScraperThread )
  Print Output

  """
  def __init__(self):
    self.scrapers = []
    self.workers = []
    self.dbworker = False
    self.categories = []
    self.compra_urls = Queue()
    self.compras = Queue()
    self.logger = logging.getLogger('PanaCrawler')
    self.engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra', echo=False,convert_unicode=False)
    self.session_maker = sessionmaker(bind=self.engine)

  def eat_categories(self):
    """Build a list of categories by scraping site"""
    success = False
    while not success:
      try:
        html = self.get_categories_html() 
        self.categories.extend(self.parse_categories_html(html))
        shuffle(self.categories)
        success = True
      except:
        continue

  def parse_categories_html(self,html):
    """returns an array of ints (category ids) from html"""
    soup = BeautifulSoup(html, parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

  def get_categories_html(self):
    """returns html from category listing page"""
    connection = httplib.HTTPConnection("201.227.172.42", "80", timeout=10)
    connection.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

  def live_scrapers(self):
    return len([scraper for scraper in self.scrapers if scraper.is_alive()]) 

  def spawn_scrapers(self,update=False):
    while len(self.categories) > 0:
      amount = 10 - self.live_scrapers()
      for i in range(amount):
        if len(self.categories) > 0:
          category = self.categories.pop()
          t = ScrapeThread(self.compra_urls,category,self.session_maker(),update)
          t.setDaemon(True)
          self.scrapers.append(t)
          t.start()
        else:
          return 0  
      sleep(5)

  def join_scrapers(self):
    while any([scraper.is_alive() for scraper in self.scrapers]):
      sleep(1)
    self.build_compra_urls_queue()
    self.logger.info('%i compras on queue', self.compra_urls.qsize())

  def build_compra_urls_queue(self):
    for url in self.session_maker().query(Url.Url).filter(Url.Url.visited == False).distinct().all():
      self.compra_urls.put(url)

  def live_workers(self):
    return len([worker for worker in self.workers if worker.is_alive()]) 

  def spawn_workers(self):
    for i in range(10):
      t = WorkThread(self.compra_urls,self.compras, self.session_maker() ,self.scrapers)
      t.setDaemon(True)
      self.workers.append(t)
      t.start()
    self.logger.info('workers running')

  def join_workers(self):
    self.logger.info('waiting on workers')
    while any([worker.is_alive() for worker in self.workers]):
      self.logger.info('%i compras remaining', self.compra_urls.qsize())
      sleep(5)
    self.logger.info('finished waiting on workers')

  def spawn_db_worker(self):
    if not self.dbworker or not self.dbworker.is_alive():
      self.dbworker = DBWorker(self.compras,self.workers)
      self.dbworker.setDaemon(True)
      self.dbworker.start()
      self.logger.info('db thread started')
  
  def join_db_worker(self):
    self.logger.info('waiting on db')
    while self.dbworker.is_alive():
      sleep(1)
    self.logger.info('finished waiting on db')

  def handler(self,signum, frame):
    print 'Signal handler called with signal', signum
    print 'waiting for threads to finish'
    self.join_scrapers()
    self.join_workers()
    self.join_db_worker()
    exit(0)

  def run(self,update=False):
    self.eat_categories() #scrape and store list of categories
    Url.Base.metadata.create_all(self.engine)
    Compra.Base.metadata.create_all(self.engine)
    #phase 1
    self.spawn_scrapers(update)
    self.join_scrapers()
    #phase 2
    self.spawn_workers()
    self.join_workers()
    self.spawn_db_worker()
    self.join_db_worker()
