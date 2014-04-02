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
        self.visit_compra(self.compra)
      except Empty:
        return
      except Exception as e:
        self.logger.debug('%s from %s', str(e),str(self))

    def __str__(self):
        return "<(CompraScraper: %s)>" % self.compra

    def visit_compra(self,compra):
        url_path = "/AmbientePublico/" + compra.url #append path
        html = self.get_compra_html(url_path)
        if html is not None:
            compra.html = html
            compra.visited = True
            self.compras_queue.put(compra)

    def get_compra_html(self,url):
        response = self.connection.request("GET", url, redirect=False)
        if response.status == 200:
            return response.data.decode('ISO-8859-1','ignore')
        else:
            return None
