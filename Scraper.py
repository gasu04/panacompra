import httplib, urllib
import re
import logging
import json
import urlparse
import threading
from time import sleep
from bs4 import BeautifulSoup, SoupStrainer

class ScrapeThread(threading.Thread):
  """
  Scrapes pages for a category
  Parses compra_urls from scraped html and adds them to the Queue

  Maintains a copy of the har to keep track of pages
  Increments har file to increment pagination

  """

  def __init__(self, compra_url, category):
    threading.Thread.__init__(self)
    self.data = dict(urlparse.parse_qsl(open('form.data').read()))
    self.compra_url = compra_url
    self.category = category
    self.strainer = SoupStrainer('a')
    self.pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile("(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('Scraper')

  def reset_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def get_page(self):
    return self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] 

  def run(self):
    self.reset_page()
    self.pages = self.parse_max_pages(self.get_category_page())
    self.logger.info('starting category %s [%s pages]',self.category,self.pages)
    for i in range(self.pages-1):
      self.eat_urls_for_category(self.category)
      self.increment_page()
#    self.logger.info('collected [%i/%i] pages from category %s', i+1, self.pages, str(self.category))
    self.logger.debug('%s dying', str(self))
    return

  def eat_urls_for_category(self,category):
    html = self.get_category_page()
    for url in self.parse_category_page(html):
      self.compra_url.put([url,category])

  def get_category_page(self):
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    connection = httplib.HTTPConnection("201.227.172.42", "80",timeout=20)
    connection.request("POST", "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=" + str(self.category), urllib.urlencode(self.data), headers)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    return [link.get('href') for link in links]

  def parse_max_pages(self,html):
    try:
      pages = self.pages_regex.findall(html)[0].decode('utf-8', 'ignore')
      return int(pages)
    except:
      print 'no pages'
      return 0

