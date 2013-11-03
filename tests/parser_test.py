import random
import unittest
from modules import parser
from classes.Compra import Compra
from bs4 import BeautifulSoup,SoupStrainer
from decimal import Decimal
from datetime import datetime
import urllib3

conn = urllib3.HTTPConnectionPool('201.227.172.42', maxsize=15)
url = '/AmbientePublico/VistaPreviaCP.aspx?NumLc=2012-0-01-0-08-CM-002791&esap=1&nnc=0&it=1'
url_directa = '/AmbientePublico/VistaPreviaCP.aspx?NumLc=2013-1-01-0-08-CD-007275&esap=1&nnc=0&it=1'
url_error = '/AmbientePublico/vistapreviacp.aspx?numlc=2013-1-40-0-08-cm-003718&esap=1&nnc=0&it=1'
compra_html = conn.request("GET", url).data.decode('ISO-8859-1','ignore')
compra_directa = conn.request("GET", url_directa).data.decode('ISO-8859-1','ignore')
error_html = conn.request("GET", url_error).data.decode('ISO-8859-1','ignore')
soup = BeautifulSoup(compra_html,'html.parser',parse_only=SoupStrainer('tr'), from_encoding='ISO-8859-1')
soup_error =  BeautifulSoup(error_html,'html.parser',parse_only=SoupStrainer('tr'), from_encoding='ISO-8859-1')
soup_directa = BeautifulSoup(compra_directa,'html.parser',parse_only=SoupStrainer('tr'), from_encoding='ISO-8859-1')

class TestParser(unittest.TestCase):

    def setUp(self):
        self.compra = compra_html
        self.compra_directa = compra_directa
        self.soup = soup
        self.soup_directa = soup_directa

    def test_error(self):
        self.assertTrue(parser.is_error_page(soup_error))
        self.assertFalse(parser.is_error_page(soup))

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

    def test_unicode(self):
        self.assertTrue(isinstance(parser.extract_description(self.soup),str))
        self.assertTrue(isinstance(parser.extract_entidad(self.soup),str))
        self.assertTrue(isinstance(parser.extract_proponente(self.soup),str))

if __name__ == '__main__':
    unittest.main()
