#!/usr/bin/python
import argparse
import logging
import yaml
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Compra import Compra
from modules import rails
from itertools import izip_longest

from PanaCrawler import PanaCrawler

import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')

def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--drop', dest='drop', action='store_const',const="True", default=False, help="drop db")
  parser.add_argument('--send', dest='send', action='store_const',const="True", default=False, help="send db")
  parser.add_argument('--update', dest='update', action='store_const',const="True", default=False, help="update db")
  parser.add_argument('--sync', dest='sync', action='store_const',const="True", default=False, help="sync db")
  return parser.parse_args()

args = parse_args()
url = 'http://panacompra.herokuapp.com'

def send_to_db():
  logger.info('sending compras to rails')
  engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra',  encoding='latin-1')
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  compras = session.query(Compra).all()
  compras_json = [{ 'compra[precio]':i.precio, 'compra[fecha]':i.fecha ,'compra[acto]': i.acto , 'compra[url]': i.url , 'compra[entidad]':i.entidad, 'compra[proponente]':i.proponente, 'compra[description]':i.description} for i in rails.filter_new_objects_for_resource_by_key(url,compras,'compras','acto')]
  for compra in compras_json:
    rails.create(url,'compras',compra)
  logger.info('sent %i compras to rails', len(compras_json))

def grouper(n, iterable, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

def send_many_to_db():
  logger.info('sending compras to rails')
  engine = create_engine('postgresql+psycopg2://panacompra:elpana@localhost/panacompra',  encoding='latin-1')
  session_maker = sessionmaker(bind=engine)
  session = session_maker()
  compras = session.query(Compra).all()
  compras_json = [{ 'precio':i.precio, 'fecha':i.fecha ,'acto': i.acto , 'url': i.url ,  'entidad':i.entidad, 'proponente':i.proponente, 'description':i.description} for i in rails.filter_new_objects_for_resource_by_key(url,compras,'compras','acto')]
  chunks = grouper(3000,compras_json)
  for chunk in chunks:
    rails.create_many(url,'compras',chunk)
  logger.info('sent %i compras to rails', len(compras_json))



if args.send:
  send_many_to_db()

elif args.update:
  p = PanaCrawler()
  p.run(True)

elif args.sync:
  p = PanaCrawler()
  p.run(True)
  send_to_db()

else:
  # 'application' code
  p = PanaCrawler()
  p.run()

logger.info("panacompra FINISHED!!!!")
