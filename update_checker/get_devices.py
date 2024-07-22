#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
import uuid
import hashlib
import hmac

def getWhiteList():
    timeStamp = str(int(time.time() * 100))
    nonce = str(uuid.uuid4())
    url = 'https://iot-earbuds-cn.allawntech.com/v1/earphone/new/latestWhiteList'
    data = '{"versionCode":"1001214","channel":"2","platform":"android"}'
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
    r_json = r.json()
    if r_json['code'] != 0:
        raise ValueError
    whitelist = requests.get(r_json['data']['downloadUrl']).json()
    return whitelist

def getDevice():
    whitelist = getWhiteList()
    devices = {device["name"]: device["id"] for device in whitelist["compatWhiteList"]}
    return devices


if __name__ == '__main__':
    print(getDevice())
