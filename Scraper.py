import httplib, urllib
import re
import json
import threading
from time import sleep
from bs4 import BeautifulSoup, SoupStrainer

class ScrapeThread(threading.Thread):
  def __init__(self, out_queue, category, har_path):
    threading.Thread.__init__(self)
    self.har = open(har_path,'rb').read()
    self.out_queue = out_queue
    self.category = category
    self.strainer = SoupStrainer('a')
    self.reset_har()

  def run(self):
    for i in range(1): #amount of pages to scan
      self.pull_urls_for_category(self.category)

  def pull_urls_for_category(self,category):
    html = self.get_urls_for_category_html(category)
    for url in self.parse_urls_for_category_html(html):
      self.out_queue.put(url)

  def get_urls_for_category_html(self,category):
    headers = {"Content-type": "application/x-www-form-urlencoded", "Automated": "true"}
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    try:
      connection.request("POST", "/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=" + str(category), urllib.urlencode({"file": self.har}), headers)
    except:
      print category
    response = connection.getresponse()
    data = response.read()
    connection.close()
    self.increment_har()
    return data

  def parse_urls_for_category_html(self,html):
    soup = BeautifulSoup(html, parse_only=self.strainer)
    links = soup.find_all(href=re.compile("VistaPrevia"))
    return [link.get('href') for link in links]

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

