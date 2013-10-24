import random
import unittest
from modules import parser
from bs4 import BeautifulSoup,SoupStrainer
from decimal import Decimal
from datetime import datetime

class TestParser(unittest.TestCase):

    def setUp(self):
        self.compra = open('tests/compra.html').read()
        self.compra_directa = open('tests/compra_directa.html').read()
        self.soup = BeautifulSoup(self.compra,'html.parser',parse_only=SoupStrainer('tr'))
        self.soup_directa = BeautifulSoup(self.compra_directa,'html.parser',parse_only=SoupStrainer('tr'))

    def test_precio(self):
        self.assertEqual(parser.extract_precio(self.soup), 999.00)
        self.assertEqual(parser.extract_precio(self.soup_directa), 1459500.00)

    def test_description(self):
        self.assertEqual(parser.extract_description(self.soup), unicode("SERVICIO DE ARBITRAJE EN LIGA DE BOLA SUAVE."))
        
    def test_compra_type(self):
        self.assertEqual(parser.extract_compra_type(self.soup), unicode("Compra Menor hasta B/. 3,000"))

    def test_dependencia(self):
        self.assertEqual(parser.extract_dependencia(self.soup), unicode("SEDE"))
        
    def test_unidad(self):
        self.assertEqual(parser.extract_unidad(self.soup), unicode("COMPRAS Y PROVEEDURIA"))
        
    def test_objeto(self):
        self.assertEqual(parser.extract_objeto(self.soup), unicode("Servicio"))
        
    def test_modalidad(self):
        self.assertEqual(parser.extract_modalidad(self.soup), unicode("Global"))
        
    def test_provincia(self):
        self.assertEqual(parser.extract_provincia(self.soup), unicode("PANAMA"))
        
    def test_correo_contacto(self):
        self.assertEqual(parser.extract_correo_contacto(self.soup), unicode("Cotizador1@asamblea.gob.pa"))
        
    def test_nombre_contacto(self):
        self.assertEqual(parser.extract_nombre_contacto(self.soup), unicode("ANTONIO DAVIS"))
        
    def test_telefono_contacto(self):
        self.assertEqual(parser.extract_telefono_contacto(self.soup), unicode("512-8090"))

    def test_fecha(self):
        self.assertEqual(parser.extract_fecha(self.soup), datetime.strptime("17-02-2012 12:23 PM","%d-%m-%Y %I:%M %p"))

    def test_acto(self):
        self.assertEqual(parser.extract_acto(self.soup), unicode("2012-0-01-0-08-CM-002791"))
        
    def test_entidad(self):
        self.assertEqual(parser.extract_entidad(self.soup), unicode("ASAMBLEA NACIONAL"))
        
    def test_proponente(self):
        self.assertEqual(parser.extract_proponente(self.soup), unicode("Roberto Peralta"))

if __name__ == '__main__':
    unittest.main()
