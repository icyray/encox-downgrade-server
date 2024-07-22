#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import uuid
import json
import hashlib
import hmac
import os
import sys
from get_devices import getDevice

class RemoteServer(object):
    def __init__(self, productId):
        self.productId = productId

    def getUpdate(self):
        timeStamp = str(int(time.time() * 100))
        nonce = str(uuid.uuid4())
        url = 'https://iot-earbuds-cn.allawntech.com/v1/earphone/firmwareInfo'
        data = '{"language":"zh_CN","productId":"%s","versionCode":"1001214","channel":"2","platform":"android"}' % (self.productId)
        key = '&*%earphone-OP7u3423**%$'
        sign = str(hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha1).hexdigest())
        header = {
            'appid': 'earphone',
            'ts': timeStamp,
            'nonce': nonce,
            'sv': 'v1',
            'sign': sign,
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length':'41',
            'Host': 'iot-earbuds-cn.allawntech.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/4.6.0'
        }
        r = requests.post(url=url, headers=header, data=data, timeout=10)
        self.json = r.json()
        if self.json['code'] != 0:
            raise ValueError
        self.__getInfo(self.json)
        data = {'name': self.name, 'size': self.size, 'url': self.url,'version': self.version,'info': self.info, 'deviceName': self.deviceName, 'productId': self.productId}
        return data

    def __getInfo(self,json):
        self.name = json['data']['content'][0]['name']
        self.size = json['data']['content'][0]['size']
        self.url = json['data']['content'][0]['url']
        self.version = json['data']['version']
        self.info = json['data']['updateInfo']
        self.deviceName = json['data']['name']


    def printInfo(self):
        print(f'{self.deviceName} New firmware version: \033[1;33m{self.version}\033[0m.\nFirmware size: \033[1;34m{self.size}\033[0m, url: \033[1;32m{self.url}\033[0m\n{self.name}. Update info: {self.info}.')

class LocalStorage(object):
    def __init__(self, path='data.json'):
        self.path = path
        if not os.path.exists(self.path):
            self.data = json.loads('{"version":"0","name":"","size":"","url":"","info":"","deviceName":"","productId":"","lastCheckTime":"","history":[]}')
            self.write()

    def read(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.version = self.data['version']

    def write(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def update(self, data, history):
        self.data.update(data)
        self.data['lastCheckTime'] = time.ctime()
        self.data['history'].append(history)
        self.write()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        devices_id = sys.argv[1]
        try:
            local = LocalStorage(f"{devices_id}.json")
            local.read()
            remote = RemoteServer(devices_id)
            data = remote.getUpdate()
            if remote.version > local.version:
                print(f'[{devices_id}] A new version find: {remote.version}')
                get_bin = requests.get(remote.url)
                with open(f'{devices_id}-{remote.name}','wb') as f:
                    f.write(get_bin.content)
                local.update(data=data, history=remote.json)
            else: print(f'[{devices_id}] No new version')
        except ValueError:
            print('Value Error!')
        except ConnectionResetError:
            print('SSL Connection Reset!')
        except (requests.ConnectTimeout, requests.ReadTimeout):
            print('Connect Timeout!')
    else:
        print('Firmware Update Checker for OPPO TWS')
        print('Usage: update_checker.py devices_id')
        try:
            supported_devices = getDevice()
        except:
            supported_devices = {'061410': 'OPPO Enco X', '060C10': 'OPPO Enco W51', '060810': 'OPPO Enco W31', 
                 '060410': 'OPPO Enco Free', '050410': 'OPPO Enco M31', '060414': 'OnePlus Buds', 
                 '068414': 'OnePlus Buds', '060814': 'OnePlus Buds Z', '068814': 'OnePlus Buds Z', 
                 '061C10': 'OPPO Enco Play', '061810': 'OPPO Enco Air', '062410': 'OPPO Enco Buds', 
                 '062810': 'OPPO Enco Air Lite', '062010': 'OPPO Enco Free2', '060C14': 'OnePlus Buds Pro'}
        print('Support devices: ', supported_devices)

        