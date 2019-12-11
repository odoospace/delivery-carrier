#!/usr/bin/env python2
import json
import config
import sys
import time
from uuid import uuid4
from pprint import pprint
from datetime import date
from multiprocessing import Pool
import requests
requests.packages.urllib3.disable_warnings()


class ActionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class API():
    def __init__(self, content_type='application/json'):
        c = config.DHL
        self.userId = c.userId
        self.key = c.key
        self.accountId = c.accountId
        self.url = c.url
        self.headers = {
            'Content-Type': content_type,
        }
        self.token = self.get_token()

    def get_url(self, action):
        """create full urls"""
        return '%s/%s' % (self.url, action)

    def send(self, url, data=[], bearer=False, method='post', accept='application/json', verify=False):
        """perform request"""
        method = method.lower()
        headers = self.headers
        if bearer:
            headers['Authorization'] = 'Bearer %s' % self.token['accessToken']

        if method == 'get':
            r = requests.get(url, data=data, headers=headers, verify=verify)
        else:
            r = requests.post(url, data=data, headers=headers, verify=verify)

        if r.status_code != 200 and r.status_code != 201:
            print ("Error fetch data from:", url, data, headers, r.status_code, r, r.json())
        data = r.json()
        return data

    def get_token(self):
        """get access token"""
        url = self.get_url('authenticate/api-key')
        params = {
            'userId': config.DHL.userId,
            'key': config.DHL.key
        }
        r = requests.post(url, data=json.dumps(params), headers=self.headers, verify=False)
        return r.json()

    def get_label(self, data=None):
        url = self.get_url('labels')
        uuid = str(uuid4())
        
        data_test = {
            "accountId": self.accountId,
            "labelId": uuid,
            "receiver": {
                "email": "s.krampus@lechio.com",
                "phoneNumber": "0031612345678",
                "name": {
                    "firstName": "Slab",
                    "companyName": "Lechio",
                    "lastName": "Krampus"
                },
                "address": {
                    "countryCode": "NL",
                    "number": "74",
                    "isBusiness": True,
                    "street": "Baan",
                    "city": "Rotterdam",
                    "postalCode": "3011CD"
                }
            },
            "shipper": {
                "email": "mdppds@dhlparcel.nl",
                "phoneNumber": "0031612345678",
                "name": {
                    "firstName": "Jan",
                    "lastName": "Jansen"
                },
                "address": {
                    "street": "Reactorweg",
                    "city": "Utrecht",
                    "number": "25",
                    "postalCode": "3542AD",
                    "isBusiness": True,
                    "addition": "A",
                    "countryCode": "NL"
                }
            },
            "parcelTypeKey": "SMALL",
            "pieceNumber": 1,
            "quantity": 1,
            "automaticPrintDialog": False,
            "options": [
                {
                    "key": "DOOR"
                },
                {
                    "key": "COD_CASH",
                    "input": "5"
                }
            ],
            "returnLabel": False
        }

        if not data: 
            data=data_test
        else:
            data['accountId'] = self.accountId
            data['labelId'] = uuid

        res = self.send(url, data=json.dumps(data), bearer=True, accept='application/pdf')
        return res



