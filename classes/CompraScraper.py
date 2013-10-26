import logging
import threading
from queue import Empty

class CompraScraperThread(threading.Thread):

    def __init__(self, compra, connection):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('CompraScraper')
        self.connection = connection
        self.compra = compra

    def run(self):
      try:
        self.eat_compra(self.compra)
      except Empty:
        return
      except Exception as e:
        self.logger.debug('%s from %s', str(e),str(self))

    def __str__(self):
        return "<(CompraScraper: %s)>" % self.compra

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
