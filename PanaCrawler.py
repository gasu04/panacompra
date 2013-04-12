from bs4 import BeautifulSoup, SoupStrainer
import httplib, urllib
import re
import sys
from Queue import Queue
from Scraper import ScrapeThread
from time import sleep
from Worker import WorkThread

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
    self.categories = []
    self.compra_urls = Queue()
    self.compras = Queue()

  def eat_categories(self):
    """Build a list of categories by scraping site"""
    html = self.get_categories_html() 
    self.categories.extend(self.parse_categories_html(html))
    print "Categories loaded: " + str(len(self.categories))

  def parse_categories_html(self,html):
    """returns an array of ints (category ids) from html"""
    soup = BeautifulSoup(html, parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

  def get_categories_html(self):
    """returns html from category listing page"""
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    connection.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

  def spawn_scrapers(self):
    for i in self.categories[:5]: 
      t = ScrapeThread(self.compra_urls,i,self.har_path)
      t.setDaemon(True)
      t.start()
      self.scrapers.append(t)
    print "Started " + str(len(self.scrapers)) + " scrapers"

  def join_scrapers(self):
    for thread in self.scrapers:
      thread.join()

  def spawn_workers(self):
    for i in range(5):
      t = WorkThread(self.compra_urls,self.compras,self.scrapers)
      t.setDaemon(True)
      t.start()
      self.workers.append(t)
    print "Started " + str(len(self.workers)) + " workers"

  def join_workers(self):
    for thread in self.workers:
      thread.join()

  def spawn_db_worker(self):
    # spawn a db worker
    return 1

  def update_status(self):
    sys.stdout.write("\rPending: %d | Compras: %d" % (self.compra_urls.qsize(),self.compras.qsize()))
    sys.stdout.flush()

  def clear_status(self):
    sys.stdout.write("\r                                           ")
    sys.stdout.flush()
    sys.stdout.write("\r\n")
    sys.stdout.flush()

  def begin_status_reports(self):
    while any([worker.is_alive() for worker in self.workers]):
      self.update_status()
      sleep(0.5)
    self.clear_status()

  def print_output(self):
    print "Compras loaded: %d" % self.compras.qsize()

  def run(self):
    self.eat_categories() #scrape and store list of categories
    self.spawn_scrapers()
    self.spawn_workers()
    dbw = self.spawn_db_worker()
    self.begin_status_reports()
    #dbw.join()
    self.print_output()


