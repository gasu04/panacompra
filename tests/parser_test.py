import random
import unittest
from modules import parser
from classes.Compra import Compra
from bs4 import BeautifulSoup,SoupStrainer
from decimal import Decimal
from datetime import datetime
import urllib.request
compra_html = urllib.request.urlopen('http://panamacompra.gob.pa/AmbientePublico/VistaPreviaCP.aspx?NumLc=2012-0-01-0-08-CM-002791&esap=1&nnc=0&it=1').read()
soup = BeautifulSoup(compra_html,'html.parser',parse_only=SoupStrainer('tr'))
compra_directa = open('tests/compra_directa.html')
soup_directa = BeautifulSoup(compra_directa,'html.parser',parse_only=SoupStrainer('tr'))

class TestParser(unittest.TestCase):

    def setUp(self):
        self.compra = compra_html
        self.compra_directa = compra_directa
        self.soup = soup
        self.soup_directa = soup_directa

    def test_precio(self):
        self.assertEqual(parser.extract_precio(self.soup), 999.00)
        self.assertEqual(parser.extract_precio(self.soup_directa), 1459500.00)

    def test_description(self):
        self.assertEqual(parser.extract_description(self.soup), str("SERVICIO DE ARBITRAJE EN LIGA DE BOLA SUAVE."))
        
    def test_compra_type(self):
        self.assertEqual(parser.extract_compra_type(self.soup), str("Compra Menor hasta B/. 3,000"))

    def test_dependencia(self):
        self.assertEqual(parser.extract_dependencia(self.soup), str("SEDE"))
        
    def test_unidad(self):
        self.assertEqual(parser.extract_unidad(self.soup), str("COMPRAS Y PROVEEDURIA"))
        
    def test_objeto(self):
        self.assertEqual(parser.extract_objeto(self.soup), str("Servicio"))
        
    def test_modalidad(self):
        self.assertEqual(parser.extract_modalidad(self.soup), str("Global"))
        
    def test_provincia(self):
        self.assertEqual(parser.extract_provincia(self.soup), str("PANAMÁ"))
        
    def test_correo_contacto(self):
        self.assertEqual(parser.extract_correo_contacto(self.soup), str("Cotizador1@asamblea.gob.pa"))
        
    def test_nombre_contacto(self):
        self.assertEqual(parser.extract_nombre_contacto(self.soup), str("ANTONIO DAVIS"))
        
    def test_telefono_contacto(self):
        self.assertEqual(parser.extract_telefono_contacto(self.soup), str("512-8090"))

    def test_fecha(self):
        self.assertEqual(parser.extract_fecha(self.soup), datetime.strptime("17-02-2012 12:23 PM","%d-%m-%Y %I:%M %p"))

    def test_acto(self):
        self.assertEqual(parser.extract_acto(self.soup), str("2012-0-01-0-08-CM-002791"))
        
    def test_entidad(self):
        self.assertEqual(parser.extract_entidad(self.soup), str("ASAMBLEA NACIONAL"))
        
    def test_proponente(self):
        self.assertEqual(parser.extract_proponente(self.soup), str("Roberto Peralta"))

    def test_parse_html(self):
        compra = Compra('url',1)
        compra.html =  compra_html
        acto = "2012-0-01-0-08-CM-002791"
        self.assertEqual(parser.parse_html(compra,{'acto':parser.extract_acto}).acto,acto) 

if __name__ == '__main__':
    unittest.main()
