import threading
import re
import logging
from time import sleep
from time import strptime
from time import strftime 
from Queue import Empty
from pymongo import MongoClient
import Compra
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules import mrclean 


class DBWorker(threading.Thread):
  """
  Stores Compra Objects
  """
  def __init__(self,compras_queue,workers):
    threading.Thread.__init__(self)
    self.engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra', encoding='latin-1',echo=True,convert_unicode=True)
    self.session_maker = sessionmaker(bind=self.engine)
    self.compras_queue = compras_queue
    self.workers = workers
    self.logger = logging.getLogger('DB')
    self.precio_regex = re.compile("(?:Precio.*?>.*?>[^0-9]*)([0-9,]*\.[0-9][0-9]*)") 
    self.descripcion_regex = re.compile("(?:Descripcion\">)([^<]*)")
    self.fecha_regex = re.compile("(?:Fecha de Public.*?>.*?>)([^<]*)") 
    self.acto_regex = re.compile("(?:ero de Acto:</td><td class=\"formEjemplos\">)([^<]*)")
    self.entidad_regex = re.compile("(?:Entidad:</td><td class=\"formEjemplos\">)([^<]*)") 
    self.proponente_regex = re.compile("(?:Proponente.*\n.*\n.*?Ejemplos\">)([^<]*)",re.MULTILINE)

  def run(self):
    session = self.session_maker()
    Compra.Base.metadata.create_all(self.engine)
    while True:
      try:
        html,url,category = self.compras_queue.get_nowait()
        compra = self.parse_compra_html(html,url,category)
 #       self.compras.insert(compra.to_json())
        session.add(compra)
        session.commit()
        self.compras_queue.task_done()
      except Empty:
        self.logger.debug("compra queue empty")
        if any([worker.is_alive() for worker in self.workers]):
          self.logger.debug("db worker going to sleep 5 seconds")
          sleep(5)
          continue
        else:
          return

  def get_regexes(self):
    return [variable for variable in self.__dict__.keys() if "_regex" in variable]


  def parse_compra_html(self,html,url,category):
    data = {}
    for regex in self.get_regexes():
      key = regex.split('_')[0] #get regex name
      try:
        val = self.__dict__[regex].findall(html)[0]
      except IndexError:
        self.logger.debug("%s not found in %s",key,url)
        val = 'empty'
      if key == "fecha":
        val = mrclean.parse_date(val)
      if key == 'precio':
        val = mrclean.parse_precio(val)
      if key == 'description':
        val = mrclean.sanitize(val)
      data[key] = val

    return Compra.Compra(url,category,html,data)
