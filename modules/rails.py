import requests
import inflect
import json
import logging
import urllib2
import os
from time import sleep

logger = logging.getLogger('rails')
headers = {'content-type': 'application/json', 'charset':'latin-1'}

def create(url,resource_name,obj,token=False):
    '''creates objects of a resource'''
    url = '/'.join([url, resource_name+'.json'])
    #url = url + ('?token=%s' % token)
    data = json.dumps(obj, encoding='latin-1')
    response = requests.post(url, data=data, headers=headers, auth=(os.environ['admin_user'],os.environ['admin_pass']))
    if response.status_code == 201:
      logger.debug('created %s from %s', resource_name, str(obj))
    else:
      logger.error('error creating %s from %s', resource_name, str(obj))
    return response

def create_many(url,resource_name,objs,token=False):
    '''creates many objects of a resource using bulk upload'''
    objs = filter(lambda x: x != None,objs)
    url = '/'.join([url, resource_name, 'create_many.json'])
    #url = url + ('?token=%s' % token)
    data = json.dumps(objs, encoding='latin-1')
    response = requests.post(url, data=data, headers=headers, auth=(os.environ['admin_user'],os.environ['admin_pass']))
    if response.status_code == 201:
      logger.debug('created %i objects of %s', len(objs), resource_name)
    else:
      logger.error('error creating %i objects of %s',len(objs), resource_name)
    return response

def index(url,resource_name,token=False):
    '''returns json document with all objects of resource'''
    url = '/'.join([url, resource_name, 'all.json'])
    #url = url + ('?token=%s' % token)
    response = requests.get(url, auth=(os.environ['admin_user'],os.environ['admin_pass']), headers=headers)
    return response.json()

def filter_new_objects_for_resource_by_key(url,objects,resource,key,token=False):
  '''returns only new objects'''
  old_objects = {el[key] for el in index(url,resource,token)}
  dupes = lambda x: x[1].encode('latin-1', 'ignore') not in old_objects
  return filter(dupes,objects)   

