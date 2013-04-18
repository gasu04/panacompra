import threading
from time import sleep
from Queue import Empty
from pymongo import MongoClient

class DBWorker(threading.Thread):
  """
  Stores Compra Objects
  """
  def __init__(self,compras_queue,workers):
    threading.Thread.__init__(self)
    self.client = MongoClient()
    self.db = self.client.panacompras
    self.compras = self.db.compras
    self.compras_queue = compras_queue
    self.workers = workers

  def run(self):
    while True:
      try:
        compra = self.compras_queue.get_nowait()
        self.compras_queue.task_done()
        self.compras.insert(compra.to_json())
      except Empty:
        sleep (1)
        if any([worker.is_alive() for worker in self.workers]):
          continue
        else:
          return


