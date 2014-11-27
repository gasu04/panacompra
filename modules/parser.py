import re
from decimal import Decimal
from datetime import datetime
from bs4 import BeautifulSoup,SoupStrainer
import logging
from classes.Compra import *

logger = logging.getLogger('Parser')

def max_pages_from_html(html):
    pages_regex = re.compile("(?:TotalPaginas\">)([0-9]*)")
    html = html.decode('ISO-8859-1','ignore')
    maxp = int(pages_regex.findall(html)[0])
    return maxp

def links_from_category_html(html):
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all(href=re.compile("VistaPreviaCP.aspx\?NumLc"))
    links = {link.get('href').lower() for link in links if link.get('href').lower()}
    return links

def is_error_page(soup):
    error = soup.find(text=re.compile("unhandled exception"))
    error2 = soup.find(text=re.compile("internal server error"))
    if error or error2 or len(soup) == 0:
        return True
    return False

def parse_compra_html(html,methods):
    soup = BeautifulSoup(html,'lxml')
    compra = {}
    if not is_error_page(soup):
        for name,method in methods.items():
            try:
                compra[name] = method(soup)
            except Exception as e:
                logger.error('error getting %s from %s', name, compra.url)
        compra['parsed'] = True
        compra['html'] = html
        aqs = get_aquisitions(soup)
        return Compra(compra),aqs

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
  string = string.replace('\n', ' ').replace('\r', '').strip().lower()
  return ' '.join(string.split()) #no repeated spaces

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

def get_aquisitions(soup):
    aqs = extract_aquisition_rows(soup)
    return [parse_aquisition_row(r) for r in aqs]

def extract_aquisition_rows(soup):
   rows = soup.find('td',text='Bien/Servicio/Obra Seleccionados').parent.find_next_sibling('tr').find_all('tr')[1:]
   return rows

def parse_aquisition_row(soup):
   tds = soup.find_all('td')
   levels = tds[1].get('title').splitlines()
   l_parse = lambda x: x.split(':')[1].strip()
   return build_aquisition([td.text for td in tds],[l_parse(l) for l in levels])

def build_aquisition(data,meta):
   aquisition = {
        'codigo':int(data[1]),
        'clasificacion':sanitize(data[2]),
        'cantidad':int(data[3]),
        'unidad':sanitize(data[4]),
        'descripcion':sanitize(data[5]),
        'ses':sanitize(data[6]),
        'categoria_1':sanitize(meta[0]),
        'categoria_2':sanitize(meta[0]),
        'categoria_3':sanitize(meta[2])
   }
   if aquisition['ses'] == '---':
        aquisition['ses'] = None
   return Adquisicion(aquisition)

def html_to_compra(html):
    modules = {
        'precio': extract_precio,
        'description': extract_description,
        'compra_type': extract_compra_type,
        'dependencia': extract_dependencia,
        'unidad': extract_unidad,
        'objeto': extract_objeto,
        'modalidad': extract_modalidad,
        'provincia': extract_provincia,
        'correo_contacto': extract_correo_contacto,
        'nombre_contacto': extract_nombre_contacto,
        'telefono_contacto': extract_telefono_contacto,
        'fecha': extract_fecha,
        'acto': extract_acto,
        'entidad': extract_entidad,
        'proponente': extract_proponente,
        'proveedor': extract_proponente
    }
    compra,aqs = parse_compra_html(html,modules)
    return compra,aqs
