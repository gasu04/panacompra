import requests
import inflect
import json
import logging
import urllib2
from StringIO import StringIO
import gzip
from time import sleep

logger = logging.getLogger('rails')
def create(url,resource_name,obj,token=False):
    '''creates objects of a resource'''
    url = '/'.join([url, resource_name+'.json'])
#   url = url + ('?token=%s' % token)
    response = requests.post(url, data=obj)
    if response.status_code == 201:
      logger.debug('created %s from %s', resource_name, str(obj))
    else:
      logger.error('error creating %s from %s', resource_name, str(obj))
    return response

def create_many(url,resource_name,objs,token=False):
    '''creates many objects of a resource using bulk upload'''
    url = '/'.join([url, resource_name, 'create_many.json'])
#   url = url + ('?token=%s' % token)
    headers = {'content-type': 'application/json', 'charset':'latin-1'}
    data = json.dumps(objs, encoding='latin-1')
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 201:
      logger.debug('created %i objects of %s', len(objs), resource_name)
    else:
      logger.error('error creating %i objects of %s',len(objs), resource_name)
    return response

def index(url,resource_name,token=False):
    '''returns json document with all objects of resource'''
    url = '/'.join([url, resource_name, 'all.json'])
#   url = url + ('?token=%s' % token)
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)
    if response.info().get('Content-Encoding') == 'gzip':
      buf = StringIO( response.read())
      f = gzip.GzipFile(fileobj=buf)
      data = f.read()
    else:
      data = response.read()
    return json.loads(data)

def show(url,resource_name,resource_id,token):
    '''returns json document with a specific object from a resource'''
    url = '/'.join([url, resource_name, str(resource_id)]) +'.json' + '?auth_token=' + token
    response = requests.get(url)
    if response.status_code == 200:
      logger.debug('showed %s with id %i', resource_name, int(resource_id))
    else:
      logger.error('error showing %s with id %i', resource_name, int(resource_id))
    return response.json()

def update(url,resource_name,resource_id,obj,token):
    '''updates an object with id of a resource'''
    auth = {'auth_token':token}
    url = '/'.join([url, resource_name, str(resource_id)]) +'.json'
    headers = {'content-type': 'application/json'}
    response = requests.put(url, params=auth ,data=json.dumps(obj), headers=headers)
    if response.status_code == 204:
      logger.debug('updated %s with id %i to %s', resource_name, int(resource_id), str(obj))
    else:
      logger.error('error updating %s with id %i to %s', resource_name, int(resource_id), str(obj))
    return response.json()

def filter_new_objects_for_resource_by_key(url,objects,resource,key,token=False):
  '''returns only new objects'''
  old_objects = {el[key] for el in index(url,resource,token)}
  dupes = lambda x: x[1].encode('latin-1', 'ignore') not in old_objects
  return filter(dupes,objects)   

