#!/usr/bin/python
import argparse
import logging
import yaml
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Compra import Compra
from modules import rails

from PanaCrawler import PanaCrawler

def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--drop', dest='drop', action='store_const',const="True", default=False, help="drop db")
  parser.add_argument('--send', dest='send', action='store_const',const="True", default=False, help="send db")
  return parser.parse_args()

args = parse_args()

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')

if args.send:
  #send to db
  engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra',  encoding='utf-8', echo=True)
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  compra = {'compra_id': 1,'categoria':44 ,'entidad': 'MEF', 'proponente':'Super 99', 'precio':10.10, 'url':'asdasdasdasd.com','acto':'123aaa','description':'asd122dasd1f1g', 'fecha':'07/02/1990'}
  arr = []
  for i in session.query(Compra):
    arr.append({ 'precio':i.precio, 'categoria':i.category, 'entidad':i.entidad})
    print i.entidad
  rails.create_many('http://localhost:3000','compras',arr)

else:
  # 'application' code
  p = PanaCrawler()
  p.run()

logger.info("panacompra FINISHED!!!!")
