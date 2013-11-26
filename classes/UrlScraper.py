import urllib.request, urllib.parse, urllib.error
import re
import logging
import urllib.parse
import threading
from bs4 import BeautifulSoup, SoupStrainer
from classes.Compra import Compra

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
    self.category = category
    self.pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    self.current_regex= re.compile("(?:PaginaActual\">)([0-9]*)")
    self.logger = logging.getLogger('UrlScraper')
    self.connection = connection
    self.urls = urls
    self.compras_queue = compras_queue
    self.base_url = "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro="
    self.parse_har()

  def parse_har(self):
    with open('form.data') as har:
        self.data = dict(urllib.parse.parse_qsl(har.read()))

  def reset_page(self,pages):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidTotalPaginas'] = int(pages)
  
  def increment_page(self):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1 + int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])
  
  def set_page(self,page):
    self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = int(page)

  def get_page(self):
    return int(self.data['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'])

  def run(self):
    self.parse_max_pages()
    self.logger.debug('starting category %s [%s pages]',self.category,len(self.pages))
    while self.pages:
      try:
        self.set_page(self.pages[-1]) #set to next page
        self.visit_urls_for_category() #visit page
        self.pages.pop() # pop page
      except Exception as e:
        self.logger.info('%s from %s', str(e),str(self))
    self.logger.info('%s dying', str(self))
    return

  def visit_urls_for_category(self):
    html = self.get_category_page()
    for url in self.parse_category_page(html):
      compra = Compra(url,self.category)
      compra = self.visit_compra(compra)
      self.compras_queue.put(compra)

  def get_category_page(self):
    response = self.connection.request("POST", str(self.base_url) + str(self.category), self.data)
    return response.data.decode('ISO-8859-1','ignore')

  def parse_category_page(self,html):
    soup = BeautifulSoup(html, "html.parser")
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
    self.reset_page(len(pages))

  def visit_compra(self,compra):
    url_path = "/AmbientePublico/" + compra.url #append path
    compra.html = self.get_compra_html(url_path)
    compra.visited = True
    return compra

  def get_compra_html(self,url):
    response = self.connection.request("GET", url)
    return response.data.decode('ISO-8859-1','ignore')
  
  def __str__(self):
    return "<(UrlScraper: category[%i])>" % (int(self.category))

