from bs4 import BeautifulSoup, SoupStrainer
import httplib, urllib
import re
import sys
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
  def __init__(self,har_path):
    self.har_path = har_path
    self.scrapers = []
    self.workers = []
    self.dbworker = False
    self.categories = []
    self.compra_urls = Queue()
    self.compras = Queue()
    self.client = MongoClient()

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

  def spawn_scrapers(self,begin,end):
    for i in self.categories[begin:end]: 
      t = ScrapeThread(self.compra_urls,i,self.har_path)
      t.setDaemon(True)
      t.start()
      self.scrapers.append(t)

  def join_scrapers(self):
    for thread in self.scrapers:
      thread.join()
      self.scrapers.remove(thread)

  def spawn_workers(self):
    for i in range(15 - len(self.workers)):
      t = WorkThread(self.compra_urls,self.compras,self.scrapers)
      t.setDaemon(True)
      t.start()
      self.workers.append(t)

  def join_workers(self):
    for thread in self.workers:
      thread.join()
      self.workers.remove(thread)

  def spawn_db_worker(self):
    if not self.dbworker:
      self.dbworker = DBWorker(self.compras,self.workers)
      self.dbworker.setDaemon(True)
      self.dbworker.start()

  def clear_status(self):
    sys.stdout.write("\r                                                                                                            ")
    sys.stdout.flush()

  def begin_status_reports(self,status):
    last_count = self.client.panacompras.compras.count()
    while any([scraper.is_alive() for scraper in self.scrapers]):
      this_count = self.client.panacompras.compras.count()
      sys.stdout.write("\rtotal: %d compras | speed: %d c/s | status: %s          " % (this_count,((this_count-last_count)/2),status))
      last_count = self.client.panacompras.compras.count()
      sys.stdout.flush()
      sleep(2)
    self.clear_status()

  def run(self):
    self.client.panacompras.compras.drop() #clear table
    self.eat_categories() #scrape and store list of categories
    for i in range(len(self.categories)):
      self.spawn_scrapers(i,i+1)
      self.spawn_workers()
      self.spawn_db_worker()
      self.begin_status_reports(str(i/56 * 100) + "%")
      self.join_scrapers()
    self.begin_status_reports("waiting on worker threads")
    self.dbworker.join()

