import urllib.request, urllib.parse, urllib.error
import re
import logging
import urllib.parse
import threading
from bs4 import BeautifulSoup, SoupStrainer
from classes.Compra import Compra
from random import shuffle

class UrlScraperThread(threading.Thread):
  """
  Scrapes pages for a category
  Parses compra_urls from scraped html and adds them to the Queue

  Maintains a copy of the har to keep track of pages
  Increments har file to increment pagination

  """

  def __init__(self, category, compras_queue, connection, urls, update=False):
    threading.Thread.__init__(self)
    self.update = update
    self.data = dict(urllib.parse.parse_qsl(open('form.data').read()))
    self.category = category
    self.pages_regex = re.compile(b"(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile(b"(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('UrlScraper')
    self.connection = connection
    self.urls = urls
    self.compras_queue = compras_queue
    self.base_url = "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro="

  def reset_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])
  
  def set_page(self,page):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = int(page)

  def get_page(self):
    return int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def run(self):
    self.reset_page()
    self.parse_max_pages()
    shuffle(self.pages)
    self.logger.debug('starting category %s [%s pages]',self.category,len(self.pages))
    while self.pages:
      try:
        current_page = self.pages.pop()
        self.set_page(current_page)
        self.eat_urls_for_category(self.category)
      except Exception as e:
        self.pages.append(current_page)
        self.logger.debug('%s from %s', str(e),str(self))
        continue
    self.logger.debug('%s dying', str(self))
    return

  def eat_urls_for_category(self,category):
    for url in self.parse_category_page(self.get_category_page()):
      compra = Compra(url,category)
      compra = self.eat_compra(compra)
      self.compras_queue.put(compra)

  def get_category_page(self):
    response = self.connection.request("POST", str(self.base_url) + str(self.category), self.data)
    return response.data

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    links = [link.get('href').lower() for link in links if link.get('href').lower() not in self.urls]
    return links

  def parse_max_pages(self):
    if self.update:
      pages = 1 
    else:
      html = self.get_category_page()
      pages = self.pages_regex.findall(html)[0]
    self.pages = [i + 1 for i in range(int(pages))]
  
  def __str__(self):
    return "<(UrlScraper: category[%i], pending[%i])>" % (int(self.category), (len(self.pages)))

  def eat_compra(self,compra):
    url_path = "/AmbientePublico/" + compra.url #append path
    compra.html = self.get_compra_html(url_path)
    compra.visited = True
    return compra

  def get_compra_html(self,url):
    try:
        response = self.connection.request("GET", url)
        data = response.data
    except Exception as e:
        self.logger.debug('%s from %s',str(e) ,str(self))
    return data
