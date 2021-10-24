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

PORT = 8090
POST_URL = 'http://smarthome.iot.oppomobile.com/v1/earphone/firmwareInfo'
GET_URL = 'http://sdk-smarthome.nearme.com.cn/firmware.bin'
UPGRADE_VERSION = '500'
data = {
    'code': 0,
    'data': {
        'content': [{
            'name': f'1_all_{UPGRADE_VERSION}_0.bin',
            'size': '__firmware_size__',
            'url': GET_URL
        }],
        'name': '__product_name__',
        'productId': '__product_id__',
        'updateInfo': '降级代理成功！酷安@icyray',
        'version': UPGRADE_VERSION
    },
    'msg': '成功'
}

class Firmware:
    def __init__(self, path='firmware.bin'):
        self.path = path
        self.type = self.get_type()
        self.version = '0'
        self.id = 'Unknown'
        self.name = 'Unknown'

    def get_type(self):
        # 0: 未加密, 1: v1加密, 2: v2加密, -1: 无效固件
        plain = b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00'
        type1 = b'\x63\x17\x53\xA0\xE2\x08\x7E\x54'
        with open(self.path, 'rb') as f:
            head = f.read(16)
            f.seek(32)
            sign = f.read(32)
        if head[:12] == plain:
            return 0
        elif head[:8] == type1:
            return 1
        elif sign.isascii():
            return 2
        else:
            return -1

    def decrypt(self):
        if self.type <= 0:
            raise Exception('非加密固件！')
        elif self.type == 1:
            with open(self.path, 'rb') as enc, open(f'dec_{self.path}', 'wb') as dec:
                key = b'\xda\x75\x15\xfb\xbc\x25\x9d\xb3'
                enc_data = enc.read()

                cipher = DES.new(key,DES.MODE_ECB)
                dec_data = cipher.decrypt(enc_data)
                dec.write(dec_data)

        elif self.type == 2:
            with open(self.path, 'rb') as enc, open(f'dec_{self.path}', 'wb') as dec:
                key = enc.read(32)
                #sign = f.read(32)
                enc.seek(64)
                iv = enc.read(16)
                enc_data = enc.read()

                cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
                dec_data = cipher.decrypt(enc_data)
                lf = dec_data[-32:].count(b'\x10')
                if lf:
                    dec.write(dec_data[:-lf])
                else:
                    dec.write(dec_data)
        self.path = f'dec_{self.path}'

        if self.get_type():
            raise Exception('解密固件失败！')

    def get_name(self, id):
        supported_devices = {'061410': 'OPPO Enco X', '060C10': 'OPPO Enco W51', '060810': 'OPPO Enco W31', 
                             '060410': 'OPPO Enco Free', '050410': 'OPPO Enco M31', '060414': 'OnePlus Buds', 
                             '068414': 'OnePlus Buds', '060814': 'OnePlus Buds Z', '068814': 'OnePlus Buds Z', 
                             '061C10': 'OPPO Enco Play', '061810': 'OPPO Enco Air', '062410': 'OPPO Enco Buds', 
                             '062810': 'OPPO Enco Air Lite', '062010': 'OPPO Enco Free2', '060C14': 'OnePlus Buds Pro'}
        return supported_devices.get(id, 'Unknown')

    def update_data(self):
        data['data']['content'][0]['size'] = str(os.path.getsize(self.path))
        data['data']['productId'] = self.id
        data['data']['name'] = self.name
        data['data']['updateInfo'] += f'\\n当前固件版本: {self.version}，适用于: {self.name}'
        
    def get_info(self):
        with open(self.path, 'rb') as f:
            f.seek(-512, os.SEEK_END)
            fb = f.read()
        firminfo = re.search(rb'(?:CHIP=(?P<chip>\w+)[\r\n]+)(?:(?!SW_VER)\S+=\S+[\r\n]+)*(?:SW_VER=(?P<ver>\S+)[\r\n]+){0,1}(?:(?!PID|PRODUCT_ID)\S+=\S+[\r\n]+)*(?:(?:PID=0X|PRODUCT_ID=0x)(?P<id>\w+)[\r\n]+){0,1}[\s\S]*?(?:REV_INFO=\S*:(?P<info>\w+))', fb)
        if firminfo:
            if firminfo.group('ver'):
                self.version = str(firminfo.group('ver').decode())
            if firminfo.group('id'):
                self.id = str(firminfo.group('id').decode())
                self.name = str(self.get_name(self.id))
        self.update_data()


class Proxy(SimpleHTTPRequestHandler):
    def do_POST(self):
        self.log_request()
        if self.path == POST_URL:
            req_datas = json.loads(self.rfile.read(int(self.headers['content-length'])).decode())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if req_datas['productId'] == firmware.id or firmware.id == 'Unknown':
                self.log_message('***** 已捕获升级请求！ *****')
                self.wfile.write(json.dumps(data).encode())
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
        if firmware.type < 0:
            print('该固件为无效固件！')
            sys.exit(1)
        elif firmware.type == 0:
            print('检测到未加密固件！')
        elif firmware.type > 0:
            print('检测到加密固件！')
            print(f'固件加密类型为 v{firmware.type} 加密，尝试解密中...')
            firmware.decrypt()
            print(f'固件解密成功，已保存为 {firmware.path} ！')

        print('尝试读取固件信息...')
        firmware.get_info()
        print(f'固件读取完毕，固件版本号: {firmware.version}，适用设备 ID: {firmware.id}，设备名: {firmware.name}.')
        if firmware.version == 0 or firmware.name == 'Unknown':
            print('当前固件不包含适用设备信息或不完整，请谨慎操作！')
            

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        with socketserver.ThreadingTCPServer(('', PORT), Proxy) as httpd:
            print(f'已启动降级代理服务器，端口：{PORT}')
            httpd.serve_forever()
            
    except FileNotFoundError:
        print('请将 firmware.bin 放置在本目录下。')
    except Exception as e:
        print(e)
    finally:
        if platform.system() == 'Windows':
            os.system('pause')