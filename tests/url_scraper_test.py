import random
import unittest
from modules import parser
from classes.Compra import Compra
from bs4 import BeautifulSoup,SoupStrainer
from queue import Queue
from classes.UrlScraper import UrlScraperThread
import urllib3
import urllib

conn = urllib3.HTTPConnectionPool('201.227.172.42', maxsize=15)
url = '/AmbientePublico/VistaPreviaCP.aspx?NumLc=2012-0-01-0-08-CM-002791&esap=1&nnc=0&it=1'
compra_url = '/VistaPreviaCP.aspx?NumLc=2012-0-01-0-08-CM-002791&esap=1&nnc=0&it=1'
compra_html_raw = conn.request("GET", url).data
compra_html_decoded = compra_html_raw.decode('ISO-8859-1','ignore')
with open('form.data') as har:
    har_dict = dict(urllib.parse.parse_qsl(har.read()))

class TestParser(unittest.TestCase):

    def setUp(self):
        self.compras_queue = Queue()
        self.urls = set()
        self.category = 70
        self.compra = Compra(compra_url,self.category)
        self.thread = UrlScraperThread(self.category, self.compras_queue, conn, self.urls)

    def test_parse_har(self):
        self.assertIsNotNone(self.thread.data)
        self.assertEqual(self.thread.data,har_dict)

    def test_get_page(self):
        page = self.thread.get_page()
        self.assertEqual(page,5)

    def test_reset_page(self):
        self.thread.reset_page()
        page = self.thread.get_page()
        self.assertEqual(page, 1)

    def test_set_page(self):
        page = self.thread.set_page(989)
        page = self.thread.get_page()
        self.assertEqual(page, 989)

    def test_get_compra_html(self):
        html = self.thread.get_compra_html(url)
        self.assertEqual(html,compra_html_decoded)
        self.assertNotEqual(html,compra_html_raw)

    def test_eat_compra(self):
        self.assertIsNone(self.compra.html)
        compra = self.thread.eat_compra(self.compra)
        self.assertIs(compra,self.compra)
        self.assertTrue(compra.visited)
        self.assertIsNotNone(compra.html)
        self.assertEqual(compra.html,compra_html_decoded)


if __name__ == '__main__':
    unittest.main()
