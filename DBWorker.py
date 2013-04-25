import threading
import re
import logging
from time import sleep
from time import strptime
from time import strftime 
from Queue import Empty
from pymongo import MongoClient
from Compra import Compra

class DBWorker(threading.Thread):
  """
  Stores Compra Objects
  """
  def __init__(self,compras_queue,workers,client):
    threading.Thread.__init__(self)
    self.client = client
    self.db = self.client.panacompras
    self.compras = self.db.compras
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
    while True:
      try:
        html,url,category = self.compras_queue.get_nowait()
        compra = self.parse_compra_html(html,url,category)
        self.compras.insert(compra.to_json())
        self.compras_queue.task_done()
      except Empty:
        self.logger.debug("compra queue empty")
        if any([worker.is_alive() for worker in self.workers]):
          self.logger.debug("db worker going to sleep 60 seconds")
          sleep(60)
          continue
        else:
          return

  def get_regexes(self):
    return [variable for variable in self.__dict__.keys() if "_regex" in variable]

  def sanitize(self,string):
    no_quotes_or_newlines = string.replace('"', '').replace("'","").replace('\n',' ').replace('\r',' ').strip() 
    return re.sub(' +',' ', no_quotes_or_newlines) #no repeated spaces

  def parse_compra_html(self,html,url,category):
    data = {}
    for regex in self.get_regexes():
      key = regex.split('_')[0] #get regex name
      try:
        val = self.__dict__[regex].findall(html)[0].decode('utf-8','ignore')
      except IndexError:
        self.logger.debug("%s not found in %s",key,url)
        val = 'empty'
      except UnicodeDecodeError:
        try:
          val = self.__dict__[regex].findall(html)[0].split()[0].decode('utf-8','ignore')
        except:
          logger.debug("%s could not be decoded in %s",val,url)
          val = 'empty'
      if key == "fecha":
        try:
          val = val.replace('.','')
          time = strptime(val,"%d-%m-%Y %I:%M %p") 
          data['time'] = strftime("%H:%M",time)
          val = strftime("%d/%m/%Y",time)
        except:
          self.logger.debug('could not get fecha in %s', url)
          val = 'empty'

      data[key] = self.sanitize(val)
    return Compra(url,category,html,data)
