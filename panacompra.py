#!/usr/bin/python2.7
import argparse
import logging
import yaml
import logging.config
import os
from modules import db_worker,crawler

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')


def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--update', dest='update', action='store_const',const="True", default=False, help="only scrape first page of every category")
  parser.add_argument('--reparse', dest='reparse', action='store_const',const="True", default=False, help="set parsed to False and parse")
  parser.add_argument('--revisit', dest='revisit', action='store_const',const="True", default=False, help="set visited to False and visit")
  parser.add_argument('--visit', dest='visit', action='store_const',const="True", default=False, help="get html for compras where visited is False")
  parser.add_argument('--pending', dest='pending', action='store_const',const="True", default=False, help="process compras where visited is True and Parsed is False")
  return parser.parse_args()

args = parse_args()

if args.update:
  crawler.run(True)
  db_worker.process_pending()
elif args.visit:
  crawler.visit_pending()
elif args.revisit:
  crawler.revisit()
elif args.reparse:
  db_worker.reparse()
elif args.pending:
  db_worker.process_pending()
else:
  crawler.run()
  db_worker.process_pending()

logger.info("panacompra FINISHED!!!!")
