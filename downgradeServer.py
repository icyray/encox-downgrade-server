#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import SimpleHTTPRequestHandler
from Crypto.Cipher import DES
from Crypto.Cipher import AES
import socketserver
import json
import os
import sys
import platform
import re
import hashlib
from enum import Enum

from update_checker.get_devices import getDevice

PORT = 8090
POST_PATTERN = r'^http:\/\/[\w.-]+\/v1\/earphone\/firmwareInfo$'
GET_URL = 'http://sdk-smarthome.nearme.com.cn/firmware.bin'
UPGRADE_VERSION = '500'
resp_data = {
    'code': 0,
    'data': {
        'content': [{
            "firmwareSHA256": '__sha256__',
            'name': f'1_all_{UPGRADE_VERSION}_0.bin',
            'size': '__firmware_size__',
            'url': GET_URL
        }],
        'name': '__product_name__',
        'productId': '__product_id__',
        'updateInfo': '降级代理成功！\nSuccessfully downgraded proxy',
        'version': UPGRADE_VERSION
    },
    'msg': '成功'
}

class TypeFirmEnc(Enum):
    PLAIN = 0
    ENCRYPT_1 = 1
    ENCRYPT_2 = 2
    INVALID = -1

class Firmware:
    def __init__(self, path='firmware.bin'):
        self.path = path
        self.type = self.get_type()
        self.version = '0'
        self.id = 'Unknown'
        self.name = 'Unknown'

    def get_type(self):
        # 0: 未加密, 1: v1加密, 2: v2加密, -1: 无效固件
        plain = b'\xFF\xFF\xFF\xFF\x00'
        type1 = b'\x63\x17\x53\xA0\xE2\x08\x7E\x54'
        with open(self.path, 'rb') as f:
            head = f.read(16)
            f.seek(32)
            sign = f.read(32)
        if head[:5] == plain:
            return TypeFirmEnc.PLAIN
        elif head[:8] == type1:
            return TypeFirmEnc.ENCRYPT_1
        elif sign.isascii():
            return TypeFirmEnc.ENCRYPT_2
        else:
            return TypeFirmEnc.INVALID

    def decrypt(self):
        if self.type == TypeFirmEnc.PLAIN:
            raise Exception('非加密固件！')
        elif self.type == TypeFirmEnc.ENCRYPT_1:
            with open(self.path, 'rb') as enc, open(f'dec_{self.path}', 'wb') as dec:
                key = b'\xda\x75\x15\xfb\xbc\x25\x9d\xb3'
                enc_data = enc.read()

                cipher = DES.new(key,DES.MODE_ECB)
                dec_data = cipher.decrypt(enc_data)
                dec.write(dec_data)

        elif self.type == TypeFirmEnc.ENCRYPT_2:
            with open(self.path, 'rb') as enc, open(f'dec_{self.path}', 'wb') as dec:
                key = enc.read(32)
                #sign = f.read(32)
                enc.seek(64)
                iv = enc.read(16)
                enc_data = enc.read()

                cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
                dec_data = cipher.decrypt(enc_data)
                dec.write(dec_data.rstrip(b'\x10'))
        self.path = f'dec_{self.path}'

        if TypeFirmEnc.INVALID == self.get_type():
            raise Exception('解密固件失败！')

    def get_name_by_id(self, id):
        supported_devices = getDevice()
        return supported_devices.get(id, 'Unknown')

    def update_data(self):
        with open(self.path, 'rb') as f:
            resp_data['data']['content'][0]['firmwareSHA256'] = hashlib.sha256(f.read()).hexdigest()
        resp_data['data']['content'][0]['size'] = str(os.path.getsize(self.path))
        resp_data['data']['productId'] = self.id
        resp_data['data']['name'] = self.name
        resp_data['data']['updateInfo'] += f'\\n当前固件版本: {self.version}，适用于: {self.name}'
        
    def get_info(self):
        self.version = '0'
        self.id = '0'
        self.name = 'Unknown'
        self.code = 'Unknown'

        with open(self.path, 'rb') as f:
            f.seek(-512, os.SEEK_END)
            fb = f.read()
        firminfo = re.search(rb'(?:CHIP=(?P<chip>\w+)[\r\n]+)(?:(?!SW_VER)\S+=\S+[\r\n]+)*(?:SW_VER=(?P<ver>\S+)[\r\n]+){0,1}(?:(?!PID|PRODUCT_ID)\S+=\S+[\r\n]+)*(?:(?:PID=0X|PID=0x|PRODUCT_ID=0x)(?P<id>\w+)[\r\n]+){0,1}[\s\S]*?(?:REV_INFO=\S*:(?P<info>\w+))', fb)
        if firminfo:
            if firminfo.group('ver'):
                self.version = str(firminfo.group('ver').decode())
            if firminfo.group('id'):
                self.id = str(firminfo.group('id').decode())
                self.name = str(self.get_name_by_id(self.id))
            if firminfo.group('info'):
                self.code = str(firminfo.group('info').decode())
        self.update_data()


class Proxy(SimpleHTTPRequestHandler):
    def do_POST(self):
        self.log_request()
        if re.match(POST_PATTERN, self.path) is not None:
            req_datas = json.loads(self.rfile.read(int(self.headers['content-length'])).decode())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if req_datas['productId'] == firmware.id or firmware.id == 'Unknown':
                self.log_message('***** 已捕获升级请求！ *****')
                self.wfile.write(json.dumps(resp_data).encode())
            else:
                self.log_error('***** 不匹配的设备！此设备 ID 为 {}. *****'.format(req_datas['productId']))
                self.wfile.write(json.dumps({'code': -1, 'msg': 'Device not support!'}).encode())
        else:
            self.wfile.write(b"HTTP/1.1 404 Not Found\r\n\r\n" + b"Not Found")

    def do_GET(self):
        self.log_request()
        if self.path == GET_URL:
            self.path = firmware.path
            super().do_GET()
            self.log_message('***** 发送固件成功！ *****')
        elif self.path == 'http://proxy.test/':
            self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n' + b'The proxy is set up correctly.')
        else:
            self.wfile.write(b"HTTP/1.1 404 Not Found\r\n\r\n" + b"Not Found")


if __name__ == '__main__':
    print('警告：降级操作具有危险性，失败导致设备损坏的风险由您自行承担！')
    print('请在手机上设置代理后，使用降级版欢律刷入固件。')
    try:
        firmware = Firmware()
        if firmware.type == TypeFirmEnc.INVALID:
            print('该固件为无效固件！')
            sys.exit(1)
        elif firmware.type == TypeFirmEnc.PLAIN:
            print('检测到未加密固件！')
        else:
            print('检测到加密固件！')
            print(f'固件加密类型为 {firmware.type.name} 加密，尝试解密中...')
            firmware.decrypt()
            print(f'固件解密成功，已保存为 {firmware.path} ！')

        print('尝试读取固件信息...')
        firmware.get_info()
        print(f'固件读取完毕，固件版本号: {firmware.version}，设备代码: {firmware.code}.')
        if firmware.id != '0':
            print(f'适用设备 ID: {firmware.id}，设备名: {firmware.name}.')
        else:
            print('当前固件不包含适用设备信息或不完整，请谨慎操作！')
            
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        with socketserver.ThreadingTCPServer(('', PORT), Proxy) as httpd:
            print(f'已启动降级代理服务器，端口：{PORT}')
            httpd.serve_forever()
            
    except FileNotFoundError:
        print('请将固件重命名为 firmware.bin 放置在本目录下。')
    except Exception as e:
        print(e)
    finally:
        if platform.system() == 'Windows':
            os.system('pause')
