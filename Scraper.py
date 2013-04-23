import httplib, urllib
import re
import json
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

  def __init__(self, compra_url, category, har_path):
    threading.Thread.__init__(self)
    self.har = open(har_path,'rb').read()
    self.compra_url = compra_url
    self.category = category
    self.strainer = SoupStrainer('a')
    self.reset_har()
    self.pages_regex = re.compile("(?:TotalPaginas\"\>)([0-9]*)")

  def run(self):
    pages = self.parse_max_pages(self.get_urls_for_category_html(self.category))
    for i in range(pages):
      self.eat_urls_for_category(self.category)
    return

  def eat_urls_for_category(self,category):
    html = self.get_urls_for_category_html(category)
    for url in self.parse_urls_for_category_html(html):
      self.compra_url.put(url)

  def get_urls_for_category_html(self,category):
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    connection = httplib.HTTPConnection("201.227.172.42", "80")
    connection.request("POST", "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=" + str(category), urllib.urlencode({"file": self.har}), headers)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    self.increment_har()
    return data

  def parse_urls_for_category_html(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPrevia"))
    return [link.get('href') for link in links]

  def parse_max_pages(self,html):
    pages = self.pages_regex.findall(html)[0].decode('utf-8', 'ignore')
    return int(pages)

  def reset_har(self):
    skip = 3 if '\xef\xbb\xbf' == self.har[:3] else 0 #skip over binary header if present
    har_json = json.loads(self.har[skip:])
    har_json['log']['entries'][0]['request']['postData']['params'][18]['value'] = 1 
    self.har = json.dumps(har_json)

  def increment_har(self):
    skip = 3 if '\xef\xbb\xbf' == self.har[:3] else 0 #skip over binary header if present
    har_json = json.loads(self.har[skip:])
    har_json['log']['entries'][0]['request']['postData']['params'][18]['value'] = 1 + int(har_json['log']['entries'][0]['request']['postData']['params'][18]['value'])
    self.har = json.dumps(har_json)

