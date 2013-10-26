from bs4 import BeautifulSoup, SoupStrainer
import urllib3
from random import shuffle
import re
import logging
from queue import Queue
from classes.UrlScraper import UrlScraperThread
from classes.CompraScraper import CompraScraperThread
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
    soup = BeautifulSoup(html, parse_only=SoupStrainer('a'))
    links = soup.find_all(href=re.compile("VerDetalleRubro"))
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
            break 
    return scrapers

def spawn_compra_scrapers(compras):
    compra_scrapers = []
    threads = THREADS - active_count() + 1
    while True:
        for i in range(threads):
            try:
                t = CompraScraperThread(next(compras),connection_pool)
                t.setDaemon(True)
                compra_scrapers.append(t)
                t.start()
            except StopIteration:
               return join_threads(compra_scrapers)
        sleep(0.1)

def join_threads(threads):
    while any([thread.is_alive() for thread in threads]):
        sleep(1)
    return threads

def run(update=False):
    categories = get_categories() #scrape and store list of categories
    urls = db_worker.get_all_urls()
    compras_queue = Queue()
    scrapers = []
    logger.info('spawning %i UrlScraperThreads', THREADS)
    while len(categories) > 0:
        scrapers.extend(spawn_scrapers(categories,compras_queue,connection_pool,urls,THREADS - active_count() + 1,update))
        db_worker.process_compras_queue(compras_queue,urls)
        sleep(0.1)
    join_threads(scrapers)
    db_worker.process_compras_queue(compras_queue,urls)

def visit_pending():
    query = db_worker.query_not_visited()
    logger.info('%i compras pending', db_worker.count_not_visited())
    logger.info('spawning %i CompraScraperThreads', THREADS)
    while query.count() > 0:
        cache = query.all()
        spawn_compra_scrapers(iter(cache))
        db_worker.merge_query(query,cache)
        del cache

def revisit():
    db_worker.reset_visited()
    visit_pending()
