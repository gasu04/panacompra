import logging
import threading
from queue import Empty

class CompraScraperThread(threading.Thread):

    def __init__(self, compra, compras_queue, connection):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('CompraScraper')
        self.connection = connection
        self.compra = compra
        self.compras_queue = compras_queue

    def run(self):
      try:
        compra = self.visit_compra(self.compra)
        if compra:
            self.compras_queue.put(compra)
      except Empty:
        return
      except Exception as e:
        self.logger.debug('%s from %s', str(e),str(self))

    def __str__(self):
        return "<(CompraScraper: %s)>" % self.compra

    def visit_compra(self,compra):
        url_path = "/AmbientePublico/" + compra.url #append path
        compra.html = self.get_compra_html(url_path)
        compra.visited = True
        return compra

    def get_compra_html(self,url):
        response = self.connection.request("GET", url)
        if response.status == 200:
            return response.data.decode('ISO-8859-1','ignore')
        else:
            return None
