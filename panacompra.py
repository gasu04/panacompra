#!/usr/bin/python2.7
import argparse
import logging
import yaml
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from classes.Compra import Compra
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

db_url = os.environ['panacompra_db']

#psql setup
engine = create_engine(db_url,  encoding='latin-1',echo=False)
session_maker = sessionmaker(bind=engine)
session = session_maker()

def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--update', dest='update', action='store_const',const="True", default=False, help="only scrape first page of every category")
  parser.add_argument('--reparse', dest='reparse', action='store_const',const="True", default=False, help="reparse db")
  parser.add_argument('--revisit', dest='revisit', action='store_const',const="True", default=False, help="revisit db")
  parser.add_argument('--pending', dest='pending', action='store_const',const="True", default=False, help="process pending compras in db")
  return parser.parse_args()

args = parse_args()

def sanitize_db():
  session.query(Compra).filter(Compra.acto == None).delete()
  session.query(Compra).filter(Compra.acto == unicode('empty')).delete()

if args.update:
  crawler = PanaCrawler(engine)
  crawler.run(True)
  db_worker.process_pending(engine)
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
