from bs4 import BeautifulSoup, SoupStrainer

import httplib, urllib, urllib3
from random import shuffle
import re
import logging
import threading
import sys,os,signal
from Queue import Queue
from UrlScraper import UrlScraperThread
from time import sleep
from sqlalchemy import distinct
from sqlalchemy.orm import sessionmaker
from classes import Compra
from threading import active_count
THREADS = 15

class PanaCrawler():
  """
  Main Crawler class

  Scrapes Category Ids
  Spawns all threads ( CompraScraperThread, UrlScraperThread )
  Print Output

  """
  def __init__(self,engine):
    self.scrapers = []
    self.connection_pool = urllib3.HTTPConnectionPool('201.227.172.42',maxsize=THREADS) 
    self.categories = []
    self.compras_queue = Queue()
    self.logger = logging.getLogger('PanaCrawler')
    self.engine = engine
    self.session_maker = sessionmaker(bind=engine)

  def eat_categories(self):
    """Build a list of categories by scraping site"""
    html = self.get_categories_html() 
    self.categories.extend(self.parse_categories_html(html))
    shuffle(self.categories)

  def parse_categories_html(self,html):
    """returns an array of ints (category ids) from html"""
    soup = BeautifulSoup(html, parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

  def get_categories_html(self):
    """returns html from category listing page"""
    response = self.connection_pool.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    data = response.data
    return data

  def live_scrapers(self):
    return len([scraper for scraper in self.scrapers if scraper.is_alive()]) 

  def spawn_scrapers(self,n,update=False):
    for i in xrange(n):
        try:
            t = UrlScraperThread(self.categories.pop(),self.compras_queue,self.connection_pool,self.urls,update)
            t.setDaemon(True)
            self.scrapers.append(t)
            t.start()
        except IndexError:
            break 

  def join_scrapers(self):
    while any([scraper.is_alive() for scraper in self.scrapers]):
      sleep(10)

  def run(self,update=False):
    self.eat_categories() #scrape and store list of categories
    Compra.Base.metadata.create_all(self.engine)
    #phase 1
    self.logger.info('spawning %i UrlScraperThreads', THREADS)
    try:
      self.urls = set(zip(*self.session_maker().query(Compra.Compra.url).all())[0])
    except:
      self.urls = set()
    while len(self.categories) > 0:
      self.spawn_scrapers(THREADS - active_count() + 1,update)
      self.process_compras_queue()
      sleep(0.1)
    self.join_scrapers()
    self.process_compras_queue()

  def process_compras_queue(self):
    session = self.session_maker()
    while self.compras_queue.qsize() > 0:
      compra = self.compras_queue.get()
      if compra.url not in self.urls: 
        session.add(compra) 
        self.urls.add(compra.url)
      self.compras_queue.task_done()
    session.commit()

  def revisit(self,):
    sess = self.session_maker()
    sess.query(Compra.Compra).update({'visited':False})
    sess.commit()
    self.run()
