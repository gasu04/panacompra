#!/usr/bin/python
import sys
from time import sleep
from pymongo import MongoClient

if len(sys.argv) < 2:
  print 'ERROR: must specify time interval for benchmark'
  sys.exit(0)

client = MongoClient()
last = client.panacompras.compras.count()

while True:
  now = int(client.panacompras.compras.count())
  sys.stdout.write('\r %i compras/sec                    ' % ((now-last)/int(sys.argv[1])))
  sys.stdout.flush()
  last = now
  sleep(int(sys.argv[1]))
