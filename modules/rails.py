import requests
import inflect
import json
import logging

logger = logging.getLogger('rails')
def create(url,resource_name,obj,token):
    '''creates objects of a resource'''
    url = '/'.join([url, resource_name+'.json']) + '?auth_token=' + token
    response = requests.post(url, data=json.dumps(obj), headers={'content-type': 'application/json'})
    if response.status_code == 201:
      logger.debug('created %s from %s', resource_name, str(obj))
    else:
      logger.error('error creating %s from %s', resource_name, str(obj))
    return response.json()

def create_many(url,resource_name,objs):
    '''creates many objects of a resource using bulk upload'''
    url = '/'.join([url, resource_name, 'create_many.json'])
    response = requests.post(url, data=json.dumps(objs, ensure_ascii=False), headers={'content-type': 'application/json'})
    if response.status_code == 201:
      logger.debug('created %i objects of %s', len(objs), resource_name)
    else:
      logger.error('error creating %i objects of %s',len(objs), resource_name)
    return response.json()

def index(url,resource_name,token):
    '''returns json document with all objects of resource'''
    url = '/'.join([url, resource_name+'.json']) + '?auth_token=' + token
    response = requests.get(url)
    if response.status_code == 200:
      logger.debug('indexed %s ', resource_name)
    else:
      logger.error('error indexing %s - %s', resource_name)
    return response.json()

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
