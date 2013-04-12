#!/usr/bin/python
from PanaCrawler import PanaCrawler

p = PanaCrawler('data.har')
p.run()
p.print_compras()
