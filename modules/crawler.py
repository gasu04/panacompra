from bs4 import BeautifulSoup, SoupStrainer
import urllib3
from random import shuffle
import re
import logging
from queue import Queue
from classes.UrlScraper import UrlScraperThread
from classes.Worker import Worker
from classes.CompraScraper import CompraScraperThread
from classes.Compra import Compra
from modules import db_worker
from time import sleep
from threading import active_count

THREADS = 15
connection_pool = urllib3.HTTPConnectionPool('201.227.172.42',maxsize=THREADS) 
logger = logging.getLogger('PanaCrawler')

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

def spawn_scrapers(categories,compras_queue,connection_pool,urls,n,update=False):
    scrapers = []
    for i in range(n):
        try:
            t = UrlScraperThread(categories.pop(),compras_queue,connection_pool,urls,update)
            t.setDaemon(True)
            scrapers.append(t)
            t.start()
        except IndexError:
            logger.info('exahusted categories')
            break 
    return scrapers

def spawn_compra_scrapers(compras,compras_queue):
    compra_scrapers = []
    threads = THREADS + 2 - active_count()
    for i in range(threads):
        try:
            t = CompraScraperThread(next(compras),compras_queue,connection_pool)
            t.setDaemon(True)
            compra_scrapers.append(t)
            t.start()
        except IndexError:
           logger.info('exahusted compras')
           break
    return compra_scrapers

def join_threads(threads):
    while any([thread.is_alive() for thread in threads]):
        sleep(1)
    return threads

def run(update=False):
    scrapers = []
    compras_queue = Queue()
    categories = get_categories() #scrape and store list of categories
    urls = db_worker.get_all_urls()
    logger.info('cached %i urls', len(urls))
    worker = spawn_worker(compras_queue,urls,scrapers)
    while len(categories) > 0:
        scrapers.extend(spawn_scrapers(categories,compras_queue,connection_pool,urls,THREADS + 2 - active_count(),update))
        sleep(0.1)
    join_threads(scrapers)

def spawn_worker(html_queue,urls,scrapers):
    thread = Worker(html_queue,urls,scrapers)
    thread.setDaemon(True)
    thread.start()
    return thread

def visit_pending():
    compras_queue = Queue()
    scrapers = []
    logger.info('%i compras pending', db_worker.count_not_visited())
    logger.info('spawning %i CompraScraperThreads', THREADS)
    urls = db_worker.get_all_urls()
    cache = db_worker.query_not_visited()
    worker = spawn_worker(compras_queue,urls,scrapers)
    while len(cache) > 0: 
        scrapers.extend(spawn_compra_scrapers(iter(cache),compras_queue))
        sleep(0.1)

def revisit():
    db_worker.reset_visited()
    visit_pending()


def bruteforce():
    compras_queue = Queue()
    scrapers = []
    logger.info('spawning %i CompraScraperThreads', THREADS)
    urls = db_worker.get_all_urls()
    cache = db_worker.url_brute()
    logger.info('initializing brute')
    worker = spawn_worker(compras_queue,urls,scrapers)
    while True:
        scrapers.extend(spawn_compra_scrapers(cache,compras_queue))
        sleep(0.2)
        scrapers = list(filter(lambda x: x.is_alive(),scrapers))
