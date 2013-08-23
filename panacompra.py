#!/usr/bin/python2.7
import argparse
import logging
import yaml
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from classes.Compra import Compra
from modules import rails
from itertools import izip_longest

from classes.PanaCrawler import PanaCrawler

import os
import signal

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')

#psql setup
engine = create_engine('postgresql+psycopg2://' + os.environ['PANAUSER'] + ':' + os.environ['PANAPASS'] + '@localhost/panacompra',  encoding='latin-1')
session_maker = sessionmaker(bind=engine)
session = session_maker()

def grouper(n, iterable, fillvalue=None):
  "Collect data into fixed-length chunks or blocks"
  # grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
  args = [iter(iterable)] * n
  return izip_longest(fillvalue=fillvalue, *args)


def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--send', dest='send', action='store_const',const="True", default=False, help="send db")
  parser.add_argument('--update', dest='update', action='store_const',const="True", default=False, help="update db")
  parser.add_argument('--sync', dest='sync', action='store_const',const="True", default=False, help="sync db")
  parser.add_argument('--url', dest='url', type=str, default='http://localhost:3000')
  return parser.parse_args()

args = parse_args()


def send_to_db():
  logger.info('sending compras to rails')
  compras = session.query(Compra).all()
  compras_json = [{ 'compra[precio]':i.precio, 'compra[category_id]':i.category, 'compra[fecha]':i.fecha.isoformat() ,'compra[acto]': i.acto , 'compra[url]': i.url , 'compra[entidad]':i.entidad, 'compra[proponente]':i.proponente, 'compra[description]':i.description} for i in rails.filter_new_objects_for_resource_by_key(args.url,compras,'compras','acto')]
  for compra in compras_json:
    rails.create(args.url,'compras',compra)
  logger.info('sent %i compras to rails', len(compras_json))

def send_many_to_db():
  logger.info('sending compras to rails')
  compras_json = [{ 'precio':i.precio, 'fecha':i.fecha.isoformat() ,'acto': i.acto , 'url': i.url , 'entidad':i.entidad, 'category_id':i.category , 'proponente':i.proponente, 'description':i.description} for i in rails.filter_new_objects_for_resource_by_key(args.url,session.query(Compra).filter(Compra.parsed == True).distinct().all(),'compras','acto')]
  chunks = grouper(3000,compras_json)
  logger.info('sending %i compras in %i chunks', len(compras_json) ,len(compras_json)/3000)
  for chunk in chunks:
    rails.create_many(args.url,'compras',chunk)
  logger.info('sent %i compras to rails', len(compras_json))


if args.send:
  send_many_to_db()
elif args.update:
  crawler = PanaCrawler(engine)
  crawler.run(True)
elif args.sync:
  crawler = PanaCrawler(engine)
  crawler.run(True)
  del crawler
  send_to_db()
else:
  crawler = PanaCrawler(engine)
  crawler.run()

logger.info("panacompra FINISHED!!!!")
