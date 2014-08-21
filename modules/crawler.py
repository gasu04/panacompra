from bs4 import BeautifulSoup, SoupStrainer
import urllib3
from urllib3 import make_headers
from random import shuffle
import re
import logging
from queue import Queue
from classes.UrlScraper import UrlScraperThread
from classes.Worker import Worker
from classes.CompraScraper import CompraScraperThread
from classes.Compra import Compra
from modules import db_worker,parser
from time import sleep
from threading import active_count
import asyncio
import aiohttp
from itertools import *
import urllib

THREADS = 8
connection_pool = urllib3.HTTPConnectionPool('201.227.172.42',maxsize=THREADS)
logger = logging.getLogger('PanaCrawler')

sem = asyncio.Semaphore(50)
lock = asyncio.Lock()

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def get_categories():
    """Build a list of categories by scraping site"""
    html = get_categories_html()
    categories = parse_categories_html(html)
    shuffle(categories)
    return categories

def parse_categories_html(html):
    """returns an array of ints (category ids) from html"""
    soup = BeautifulSoup(html, 'lxml', parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
    logger.info('compras on site: %i',(sum([int(link.string) for link in links])))
    return [re.match(r"(?:.*Rubro\()([0-9]*)",link.get('href')).group(1) for link in links]

def get_categories_html():
    """returns html from category listing page"""
    response = connection_pool.request("GET", "/Portal/OportunidadesDeNegocio.aspx")
    data = response.data
    return data

def run(update=False):
    categories = get_categories() #scrape and store list of categories
    urls = db_worker.get_all_urls()
    logger.info('cached %i urls', len(urls))
    loop = asyncio.get_event_loop()
    f = asyncio.wait([get_compras_for_category(c,urls) for c in categories])
    loop.run_until_complete(f)

def revisit():
    db_worker.reset_visited()
    cache = db_worker.query_not_visited()
    crawl_urls(iter(cache))

def visit_pending():
    cache = db_worker.query_not_visited()
    crawl_urls(iter(cache))

def bruteforce():
    crawl_urls(db_worker.url_brute())

@asyncio.coroutine
def get(*args, **kwargs):
    response = yield from aiohttp.request('GET', *args, **kwargs)
    if response.status == 200 and 'error' not in response.url:
        return (yield from response.read())
    response.close()

@asyncio.coroutine
def post(*args, **kwargs):
    response = yield from aiohttp.request('POST', *args, **kwargs)
    if 'error' not in response.url:
        return (yield from response.read())
    response.close()

@asyncio.coroutine
def get_compra(url):
    url = "http://panamacompra.gob.pa/AmbientePublico/" + url
    with (yield from sem):
        html = yield from get(url, compress=True, allow_redirects=False)
    if html:
        html = html.decode('ISO-8859-1','ignore')
        compra = parser.html_to_compra(html)
        with (yield from lock):
            db_worker.create_compra(compra)

def reset_har(har,max_pages):
    har = har.copy()
    har['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = 1
    har['ctl00$ContentPlaceHolder1$ControlPaginacion$hidTotalPaginas'] = int(max_pages)
    return har

def set_har_page(har,page):
    har = har.copy()
    har['ctl00$ContentPlaceHolder1$ControlPaginacion$hidNumeroPagina'] = page
    return har

@asyncio.coroutine
def get_compras_for_category(category,urls):
   for page in (yield from pages_for_category(category)):
        url = 'http://panamacompra.gob.pa/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=' + str(category)
        html = yield from post(url, compress=True, data=page)
        for url in parser.links_from_category_html(html):
            if url not in urls:
                yield from get_compra(url)

@asyncio.coroutine
def pages_for_category(category):
    #maxp = yield from get_max_pages(category)
    maxp=5
    with open('form.data') as har:
        har = reset_har(dict(urllib.parse.parse_qsl(har.read())),maxp)
    return [set_har_page(har,i) for i in range(1,maxp+1)]

@asyncio.coroutine
def get_max_pages(category):
    url = 'http://panamacompra.gob.pa/AmbientePublico/AP_Busquedaavanzada.aspx?BusquedaRubros=true&IdRubro=' + str(category)
    html = yield from get(url)
    return parser.max_pages_from_html(html)

def crawl_urls(cache):
    lock = asyncio.Lock()
    in_chunks = filter(None,grouper(cache,10000))
    while True:
        chunk = next(in_chunks)
        loop = asyncio.get_event_loop()
        f = asyncio.wait([get_compra(compra) for compra in chunk])
        loop.run_until_complete(f)
