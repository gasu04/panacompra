import threading
import httplib, urllib
from Compra import Compra

class WorkThread(threading.Thread):
  def __init__(self, queue, out_queue):
    threading.Thread.__init__(self)
    self.compra_urls = queue
    self.compras = out_queue

  def run(self):
    url = self.compra_urls.get()
    self.pull_compra(url)
    self.compra_urls.task_done()

  def pull_compra(self,url):
    html = self.get_compra_html(url)
    self.compras.put(Compra(url,html,parse_compra_html(html)))

  def parse_compra_html(self,html):
    return [1]

  def get_compra_html(self,url):
    connection = httplib.HTTPConnection("www.panamacompra.gob.pa", "80")
    url = "/AmbientePublico/" + url #append path
    connection.request("GET", url)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return data


