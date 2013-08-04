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
  parser.add_argument('--update', dest='update', action='store_const',const="True", default=False, help="update db")
  return parser.parse_args()

args = parse_args()
url = 'http://localhost:3000'

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')

if args.send:
  #send to db
  logger.info('sending compras to rails')
  engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra',  encoding='latin-1', echo=True)
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  compras = session.query(Compra).all()
  compras_json = [{ 'precio':i.precio, 'fecha':i.fecha ,'acto': i.acto , 'url': i.url , 'category_id':i.category, 'entidad':i.entidad, 'proponente':i.proponente, 'description':i.description} for i in rails.filter_new_objects_for_resource_by_key(url,compras,'compras','acto')]
  rails.create_many(url,'compras',compras_json)
 # for i in rails.filter_new_objects_for_resource_by_key(url,compras,'compras','acto'):
  #  rails.create(url,'compras', { 'compra[precio]':i.precio, 'compra[fecha]':i.fecha ,'compra[acto]': i.acto , 'compra[url]': i.url , 'compra[category_id]':i.category, 'compra[entidad]':i.entidad, 'compra[proponente]':i.proponente, 'compra[description]':i.description})

elif args.update:
  p = PanaCrawler()
  p.run(True)

else:
  # 'application' code
  p = PanaCrawler()
  p.run()

logger.info("panacompra FINISHED!!!!")
