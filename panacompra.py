#!/usr/bin/python
from PanaCrawler import PanaCrawler
from pymongo import MongoClient

p = PanaCrawler('data.har')
p.run()

client = MongoClient()
print "Compras in DB: " + str(client.panacompras.compras.count())
