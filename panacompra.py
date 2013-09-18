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
from modules import db_worker

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
engine = create_engine('postgresql+psycopg2://' + os.environ['PANAUSER'] + ':' + os.environ['PANAPASS'] + '@localhost/panacompra',  encoding='latin-1',echo=False)
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
  parser.add_argument('--revisit', dest='revisit', action='store_const',const="True", default=False, help="revisit db")
  parser.add_argument('--reparse', dest='reparse', action='store_const',const="True", default=False, help="reparse db")
  parser.add_argument('--pending', dest='pending', action='store_const',const="True", default=False, help="pending db")
  parser.add_argument('--url', dest='url', type=str, default='http://localhost:5000')
  return parser.parse_args()

args = parse_args()


def get_new():
  return [ i.id for i in rails.filter_new_objects_for_resource_by_key(args.url,session.query(Compra.id,Compra.acto).filter(Compra.parsed == True).filter(Compra.fecha != None).distinct(),'compras','acto')]

def send_to_db():
  logger.info('sending compras to rails')
  new = get_new()
  for compra in session.query(Compra).filter(Compra.id.in_(new)):
    rails.create(args.url,'compras',compra.to_dict(),'1zWRXH7m3kgV0CV3P8wxPXN1i6zgU2Bvm4mIpaA00lFmaswla9Qj5WIOAcNPSko')
  logger.info('sent %i compras to rails', len(new))

def send_many_to_db():
  logger.info('sending compras to rails')
  n = get_new()
  m = 0
  while True:
    chunk = session.query(Compra).filter(Compra.id.in_(n)).offset(m).limit(3000).all()
    if len(chunk) == 0: break
    logger.info('sending %i compras to rails',len(chunk))
    rails.create_many(args.url,'compras',[i.to_dict() for i in chunk],'1zWRXH7m3kgV0CV3P8wxPXN1i6zgU2Bvm4mIpaA00lFmaswla9Qj5WIOAcNPSko')
    m = m + 3000
  logger.info('done sending compras to rails')

def sanitize_db():
  session.query(Compra).filter(Compra.acto == None).delete()
  session.query(Compra).filter(Compra.acto == unicode('empty')).delete()

if args.send:
  sanitize_db()
  send_many_to_db()
elif args.update:
  crawler = PanaCrawler(engine)
  crawler.run(True)
  db_worker.process_pending(engine)
elif args.sync:
  crawler = PanaCrawler(engine)
  crawler.run(True)
  del crawler
  db_worker.process_pending(engine)
  sanitize_db()
  send_to_db()
elif args.revisit:
  crawler = PanaCrawler(engine)
  crawler.revisit()
elif args.reparse:
  db_worker.reparse(engine)
elif args.pending:
  db_worker.process_pending(engine)
else:
  crawler = PanaCrawler(engine)
  crawler.run()
  db_worker.process_pending(session_maker)
  del crawler

logger.info("panacompra FINISHED!!!!")
