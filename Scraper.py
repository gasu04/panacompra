import httplib, urllib
import re
import logging
import json
import urlparse
import threading
from socket import timeout
from time import sleep
from bs4 import BeautifulSoup, SoupStrainer

class ScrapeThread(threading.Thread):
  """
  Scrapes pages for a category
  Parses compra_urls from scraped html and adds them to the Queue

  Maintains a copy of the har to keep track of pages
  Increments har file to increment pagination

  """

  def __init__(self, compra_url, category, update=False):
    threading.Thread.__init__(self)
    self.update = update
    self.data = dict(urlparse.parse_qsl(open('form.data').read()))
    self.compra_url = compra_url
    self.category = category
    self.strainer = SoupStrainer('a')
    self.pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile("(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('Scraper')
    self.connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=60)

  def reset_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def get_page(self):
    return self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] 

  def run(self):
    self.reset_page()
    if self.update:
      self.pages = 1 
    else:
      self.pages = self.parse_max_pages(self.get_category_page())
    self.logger.info('starting category %s [%s pages]',self.category,self.pages)
    for i in range(self.pages):
      try:
        self.eat_urls_for_category(self.category)
        self.increment_page()
      except timeout:
        self.logger.debug('HTTP timeout from %s', str(self))
        self.increment_page()
        continue
    self.connection.close()
    self.logger.debug('%s dying', str(self))
    return

  def eat_urls_for_category(self,category):
    html = self.get_category_page()
    for url in self.parse_category_page(html):
      self.compra_url.put([url,category])

  def get_category_page(self):
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    self.connection.request("POST", "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=" + str(self.category), urllib.urlencode(self.data), headers)
    response = self.connection.getresponse()
    data = response.read()
    return data

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    return [link.get('href') for link in links]

  def parse_max_pages(self,html):
    try:
      pages = self.pages_regex.findall(html)[0].decode('latin-1', 'ignore')
      return int(pages)
    except IndexError:
      print 'no pages'
      return 0

