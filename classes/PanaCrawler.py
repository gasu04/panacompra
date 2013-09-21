from bs4 import BeautifulSoup, SoupStrainer

import httplib, urllib
from random import shuffle
import re
import logging
import threading
import sys,os,signal
from Queue import Queue
from UrlScraper import UrlScraperThread
from time import sleep
from CompraScraper import CompraScraperThread
from modules import rails
from sqlalchemy import distinct
from sqlalchemy.orm import sessionmaker
from classes import Compra

class PanaCrawler():
  """
  Main Crawler class

  Scrapes Category Ids
  Spawns all threads ( CompraScraperThread, UrlScraperThread )
  Print Output

  """
  def __init__(self,engine):
    self.scrapers = []
    self.workers = []
    self.categories = []
    self.compras_queue = Queue()
    self.logger = logging.getLogger('PanaCrawler')
    self.engine = engine
    self.session_maker = sessionmaker(bind=engine)

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
    for category in self.categories:
      t = UrlScraperThread(category,self.session_maker(),update)
      t.setDaemon(True)
      self.scrapers.append(t)
      t.start()

  def join_scrapers(self):
    while any([scraper.is_alive() for scraper in self.scrapers]):
      sleep(10)
    self.build_compras_queue_queue()

  def build_compras_queue_queue(self):
    for compra in self.session_maker().query(Compra.Compra).filter(Compra.Compra.visited == False).distinct():
      self.compras_queue.put(compra)
    self.logger.info('%i compras on queue', self.compras_queue.qsize())

  def live_workers(self):
    return len([worker for worker in self.workers if worker.is_alive()]) 

  def spawn_workers(self):
    for i in range(40):
      t = CompraScraperThread(self.compras_queue, self.session_maker())
      t.setDaemon(True)
      self.workers.append(t)
      t.start()
    self.logger.info('workers running')

  def join_workers(self):
    self.logger.info('waiting on workers')
    while any([worker.is_alive() for worker in self.workers]):
      self.logger.info('%i compras remaining', self.compras_queue.qsize())
      sleep(15)
    self.logger.info('finished waiting on workers')

  def handler(self,signum, frame):
    print 'Signal handler called with signal', signum
    print 'waiting for threads to finish'
    self.join_scrapers()
    self.join_workers()
    exit(0)

  def run(self,update=False):
    self.eat_categories() #scrape and store list of categories
    Compra.Base.metadata.create_all(self.engine)
    #phase 1
    self.spawn_scrapers(update)
    self.join_scrapers()
    #phase 2
    self.spawn_workers()
    self.join_workers()

  def revisit(self,):
    sess = self.session_maker()
    sess.query(Compra.Compra).update({'visited':False})
    sess.commit()
    self.build_compras_queue_queue()
    self.spawn_workers()
    self.join_workers()
