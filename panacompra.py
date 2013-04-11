#!/usr/bin/python
from bs4 import BeautifulSoup, SoupStrainer
import httplib, urllib
import re
import json
from Queue import Queue
from Scraper import ScrapeThread
from Worker import WorkThread

class PanaCrawler():
  def __init__(self,har_path):
    self.har_path = har_path
    self.scrapers = []
    self.workers = []
    self.compra_urls = Queue()
    self.strainer = SoupStrainer('a')
    self.categories = []
    self.compras = Queue()

  def pull_categories(self):
    html = self.get_categories_html() 
    self.categories.extend(self.parse_categories_html(html))
    print "Categories loaded: " + str(len(self.categories))

  def parse_categories_html(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

  def get_categories_html(self):
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    connection.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

  def spawn_scrapers(self):
    for i in categories[:1]:  #change this for production 
      t = ScrapeThread(self.compra_urls,50,self.har_path)
      t.setDaemon(True)
      t.start()
      self.scrapers.append(t)

  def join_scrapers(self):
    for thread in self.scrapers:
      thread.join()

  def spawn_workers(self):
    t = WorkThread(self.compra_urls,self.compras)
    t.setDaemon(True)
    t.start()
    self.workers.append(t)

  def join_workers(self):
    for thread in self.workers:
      thread.join()

  def run(self):
    self.pull_categories()
    self.spawn_scrapers()
    self.spawn_workers()
    self.join_scrapers()
    self.join_workers()
    ########################
    #### db worker here ####
    ########################
    print "Compras loaded: " + str(self.compras.qsize())

p = PanaCrawler('data.har')
p.run()
