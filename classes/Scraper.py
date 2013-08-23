import httplib, urllib
import re
import logging
import json
import urlparse
import threading
from socket import timeout
from time import sleep
from bs4 import BeautifulSoup, SoupStrainer
from sqlalchemy.sql import exists
from classes.Compra import Compra
from Url import Url

class ScrapeThread(threading.Thread):
  """
  Scrapes pages for a category
  Parses compra_urls from scraped html and adds them to the Queue

  Maintains a copy of the har to keep track of pages
  Increments har file to increment pagination

  """

  def __init__(self, category, session, update=False):
    threading.Thread.__init__(self)
    self.update = update
    self.data = dict(urlparse.parse_qsl(open('form.data').read()))
    self.category = category
    self.strainer = SoupStrainer('a')
    self.pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile("(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('Scraper')
    self.connection = False
    self.session = session

  def reset_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def get_page(self):
    return int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def open_connection(self):
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=15)
      except:
        continue

  def reset_connection(self):
    self.connection.close()
    self.connection = False
    while not self.connection:
      try:
        self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=15)
      except:
        continue

  def run(self):
    self.reset_page()
    self.open_connection()
    self.parse_max_pages()
    self.logger.info('starting category %s [%s pages]',self.category,self.pages)
    while self.pages >= self.get_page():
      try:
        self.eat_urls_for_category(self.category)
        self.increment_page()
      except:
        self.reset_connection()
        self.logger.debug('HTTP timeout from %s', str(self))
        continue
    self.connection.close()
    self.session.close()
    self.logger.debug('%s dying', str(self))
    return

  def eat_urls_for_category(self,category):
    for url in self.parse_category_page(self.get_category_page()):
      self.session.add(Compra(url,category))
      self.session.commit()

  def get_category_page(self):
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    success = False
    while not success:
      try:
        self.connection.request("POST", "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=" + str(self.category), urllib.urlencode(self.data), headers)
        response = self.connection.getresponse()
        data = response.read()
        success = True
      except Exception as e:
        sleep(1)
        self.logger.debug('RESPONSE timeout from %s', str(self))
        self.reset_connection()
        sleep(1)
        continue
    return data

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    remove_dupes = lambda x: not self.session.query(exists().where(Compra.url==(str(x)))).scalar()
    return filter(remove_dupes,[link.get('href') for link in links])

  def parse_max_pages(self):
    if self.update:
      self.pages = 1 
    else:
      html = self.get_category_page()
      pages = self.pages_regex.findall(html)[0].decode('latin-1', 'ignore')
      self.pages = int(pages)
  
  def __str__(self):
    return "<(Scraper: category[%i], page[%i])>" % (int(self.category), int(self.get_page()))
