import re
from decimal import Decimal
from datetime import datetime
from bs4 import BeautifulSoup,SoupStrainer
import logging

logger = logging.getLogger('Parser')

def is_error_page(soup):
    error = soup.find(text=re.compile("unhandled exception"))
    error2 = soup.find(text=re.compile("internal server error"))
    if error or error2 or len(soup) == 0:
        return True
    return False

def parse_html(compra,methods):
    soup = BeautifulSoup(compra.html,'html.parser')
    if not is_error_page(soup):
        for name,method in methods.items():
            try:
                val = method(soup)
                setattr(compra,name,val)
            except Exception as e:
                logger.error('error getting %s from %s', name, compra.url)
    compra.parsed = True
    return compra 

def parse_date(date):
  try:
    date = date.replace('.','').upper()
    date = datetime.strptime(date,"%d-%m-%Y %I:%M %p") 
  except Exception as e:
    logger.error("%s", e)
    logger.error('error parsing date %s', date)
    date = None
  return date

def parse_precio(precio):
  precio = re.sub(r'[^\d.]', '',precio) #remove non digits
  precio = re.sub(r'^.', '',precio) #remove leading period
  if not precio == "":
    precio = Decimal(precio)
  else:
    precio = Decimal(0) 
  return precio

def sanitize(string):
  return str(re.sub(' +',' ', string)) #no repeated spaces

def extract_precio(soup):
    precio = soup.find(text='Precio Referencia:')
    precio_d = soup.find(text='Monto de la Contratación:')
    if precio:
        return parse_precio(precio.parent.find_next_sibling('td').string)
    elif precio_d:
        return parse_precio(precio_d.parent.find_next_sibling('td').string)
    else:
        return Decimal(0)
    
def extract_description(soup):
    a = soup.find(text='Descripción:')
    if a is not None and a.string is not None:
        return sanitize(a.parent.find_next_sibling('td').string)
    return None

def extract_compra_type(soup):
    return sanitize(soup.find('td',text='Tipo de Procedimiento:').find_next_sibling('td').string)
    
def extract_dependencia(soup):
    return sanitize(soup.find('td',text='Dependencia:').find_next_sibling('td').string)

def extract_unidad(soup):
    return sanitize(soup.find('td',text='Unidad de Compra:').find_next_sibling('td').string)
    
def extract_objeto(soup):
    return sanitize(soup.find('td',text='Objeto Contractual:').find_next_sibling('td').string)
    
def extract_modalidad(soup):
    modalidad = soup.find('td',text='Modalidad de adjudicación:')
    if modalidad is not None:
        return sanitize(modalidad.find_next_sibling('td').string)
    return None
    
def extract_provincia(soup):
    provincia = soup.find(text='Provincia de Entrega:')
    if provincia is not None:
        return sanitize(provincia.parent.find_next_sibling('td').string)
    return None
    
def extract_correo_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find('td').find_next_sibling('td').string)
    
def extract_nombre_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find('td').find_next_sibling('td').string)
    
def extract_telefono_contacto(soup):
    return sanitize(soup.find('td',text='Datos de Contacto').parent.find_next_sibling('tr').find_next_sibling('tr').find_next_sibling('tr').find('td').find_next_sibling('td').string[:14])

def extract_fecha(soup):
    return parse_date(soup.find('td',text='Fecha de Publicación:').find_next_sibling('td').string)
    
def extract_acto(soup):
    return sanitize(soup.find(text='Número de Acto:').parent.find_next_sibling('td').string)

def extract_entidad(soup):
    return sanitize(soup.find('td',text='Entidad:').find_next_sibling('td').string)
    
def extract_proponente(soup):
    proponente = soup.find('td',text='Proponente Seleccionado')
    if proponente is not None:
        return sanitize(proponente.parent.find_next_sibling('tr').find('td').find_next_sibling('td').string)
    return None

