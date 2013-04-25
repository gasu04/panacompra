from bs4 import BeautifulSoup, SoupStrainer

import httplib, urllib
import re
import sys
import logging
import threading
from Queue import Queue
from Scraper import ScrapeThread
from time import sleep
from Worker import WorkThread
from DBWorker import DBWorker
from pymongo import MongoClient


class PanaCrawler():
  """
  Main Crawler class

  Scrapes Category Ids
  Spawns all threads ( WorkerThread, ScraperThread )
  Print Output

  """
  def __init__(self, client):
    self.scrapers = []
    self.workers = []
    self.dbworker = False
    self.categories = []
    self.compra_urls = Queue()
    self.compras = Queue()
    self.client = client
    self.logger = logging.getLogger('PanaCrawler')

  def eat_categories(self):
    """Build a list of categories by scraping site"""
    html = self.get_categories_html() 
    self.categories.extend(self.parse_categories_html(html))

  def parse_categories_html(self,html):
    """returns an array of ints (category ids) from html"""
    soup = BeautifulSoup(html, parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

  def get_categories_html(self):
    """returns html from category listing page"""
    connection = httplib.HTTPConnection("201.227.172.42", "80")
    connection.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

  def live_scrapers(self):
    return len([scraper for scraper in self.scrapers if scraper.is_alive()]) 

  def spawn_scrapers(self):
    if self.categories: 
      amount = 10 - self.live_scrapers() 
      for i in range(amount):
        category = self.categories.pop()
        t = ScrapeThread(self.compra_urls,category)
        t.setDaemon(True)
        t.start()
        self.scrapers.append(t)
        self.logger.debug('scraper thread started on category %s', category)
      self.logger.debug('started %i scrapers', amount)
      

  def join_scrapers(self):
    self.logger.info('waiting on scrapers')
    while any([scraper.is_alive() for scraper in self.scrapers]):
      sleep(0.3)
    self.scrapers = []
    self.logger.info('finished waiting on scrapers')


  def live_workers(self):
    return len([worker for worker in self.workers if worker.is_alive()]) 

  def spawn_workers(self):
    amount = 20 - self.live_workers()
    if amount > 0:
      for i in range(amount):
        t = WorkThread(self.compra_urls,self.compras,self.scrapers)
        t.setDaemon(True)
        t.start()
        self.workers.append(t)
      self.logger.debug('started %i workers', amount)

  def join_workers(self):
    self.logger.info('waiting on workers')
    while any([worker.is_alive() for worker in self.workers]):
      sleep(0.3)
    self.workers = []
    self.logger.info('finished waiting on workers')

  def spawn_db_worker(self):
    if not self.dbworker or not self.dbworker.is_alive():
      self.dbworker = DBWorker(self.compras,self.workers,self.client)
      self.dbworker.setDaemon(True)
      self.dbworker.start()
      self.logger.info('db thread started')
  
  def join_db_worker(self):
    self.logger.info('waiting on db')
    while self.dbworker.is_alive():
      sleep(1)
    self.logger.info('finished waiting on db')

  def run(self):
    self.eat_categories() #scrape and store list of categories
    while self.categories:
      if threading.active_count() < 32:
        self.spawn_scrapers()
        self.spawn_workers()
        self.spawn_db_worker()
      sleep(0.5)
    self.join_scrapers()
    self.join_workers()
    self.join_db_worker()
