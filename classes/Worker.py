from modules import db_worker,parser
from threading import Thread
import logging
from queue import Empty
from bs4 import BeautifulSoup
from time import sleep

logger = logging.getLogger('worker')

def process_compra(compra):
  modules = {
    'precio': parser.extract_precio,
    'description': parser.extract_description,
    'compra_type': parser.extract_compra_type,
    'dependencia': parser.extract_dependencia,
    'unidad': parser.extract_unidad,
    'objeto': parser.extract_objeto,
    'modalidad': parser.extract_modalidad,
    'provincia': parser.extract_provincia,
    'correo_contacto': parser.extract_correo_contacto,
    'nombre_contacto': parser.extract_nombre_contacto,
    'telefono_contacto': parser.extract_telefono_contacto,
    'fecha': parser.extract_fecha,
    'acto': parser.extract_acto,
    'entidad': parser.extract_entidad,
    'proponente': parser.extract_proponente
  }
  compra = parser.parse_html(compra,modules)
  db_worker.create_compra(compra)
  return compra

class Worker(Thread): 
    def __init__(self,html_queue,scrapers): 
        Thread.__init__(self) 
        self.html_queue = html_queue 
        self.scrapers = scrapers
 
    def run(self): 
        while True: 
            try: 
                compra = self.html_queue.get(timeout=20) 
                self.html_queue.task_done() 
                compra = process_compra(compra) 
            except Empty: 
                if not any([scraper.is_alive() for scraper in self.scrapers]):
                    raise Exception('worker is dead') 
                    return 

