#!/usr/bin/python
import argparse
import logging
import yaml
import logging.config

from PanaCrawler import PanaCrawler
from pymongo import MongoClient

def parse_args():
  parser = argparse.ArgumentParser(description='Dataminer for Panacompra')
  parser.add_argument('--drop', dest='drop', action='store_const',const="True", default=False, help="drop db")
  return parser.parse_args()

args = parse_args()

# create logger
logging.config.dictConfig(yaml.load(open('logging.yaml','r').read()))
logger = logging.getLogger('panacompra')
logger.info('panacompra started')

#start db client
client = MongoClient()
if args.drop:
  client.panacompras.compras.drop()
  logger.info("panacompras.compras dropped!")

# 'application' code
p = PanaCrawler(client)
p.run()
logger.info("panacompra FINISHED!!!! - compras in DB: %s", str(client.panacompras.compras.count()))
