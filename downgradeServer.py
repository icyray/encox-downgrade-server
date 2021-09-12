#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import SimpleHTTPRequestHandler
import socketserver
import json
import os
import sys
import re

PORT = 8090
data = {
    'code': 0,
    'data': {
        'content': [{
            'name': '1_all_500_0.bin',
            'size': '__firmware_size',
            'url': 'http://sdk-smarthome.nearme.com.cn/firmware.bin'
        }],
        'name': '__product_name',
        'productId': '__product_id',
        'updateInfo': '降级代理成功！\\n酷安@icyray',
        'version': '500'
    },
    'msg': '成功'
}


class Proxy(SimpleHTTPRequestHandler):
    def do_POST(self):
        self.log_request()
        if self.path == 'http://smarthome.iot.oppomobile.com/v1/earphone/firmwareInfo':
            req_datas = json.loads(self.rfile.read(int(self.headers['content-length'])).decode())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if req_datas['productId'] == '061410' or req_datas['productId'] == '060C10':
                self.log_message('已捕获升级请求！')
                self.wfile.write(json.dumps(data).encode())
            else:
                self.log_error('不支持的设备！此设备 ID 为 {}.'.format(req_datas['productId']))
                self.wfile.write(json.dumps({'code': -1, 'msg': 'Device not support!'}).encode())
        else:
            self.wfile.write(b"HTTP/1.1 404 Not Found\r\n\r\n" + b"Not Found")

    def do_GET(self):
        self.log_request()
        if self.path == 'http://sdk-smarthome.nearme.com.cn/firmware.bin':
            self.path = '/firmware.bin'
            super().do_GET()
            self.log_message('发送固件成功！')
        elif self.path == 'http://proxy.test/':
            self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n' + b'The proxy is set up correctly.')
        else:
            self.wfile.write(b"HTTP/1.1 404 Not Found\r\n\r\n" + b"Not Found")


def get_firminfo():
    with open('firmware.bin', 'rb') as f:
        f.seek(-512, os.SEEK_END)
        fb = f.read()
    return re.search(rb'SW_VER=(\d+)\s+[\s\S]*PID=0X(\w+)\s+', fb)


def get_devicename(deviceID):
    supported_devices = {'061410': 'OPPO Enco X', '060C10': 'OPPO Enco W51'}
    return supported_devices.get(str(deviceID), '未知设备')


def update_data(firminfo):
    data['data']['content'][0]['size'] = str(os.path.getsize('./firmware.bin'))
    data['data']['productId'] = str(firminfo.group(2).decode())
    data['data']['name'] = str(get_devicename(firminfo.group(2).decode()))


if __name__ == '__main__':
    try:
        firminfo = get_firminfo()
        if not firminfo:
            print('无效固件或该固件已加密！')
            sys.exit(1)
        update_data(firminfo)

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        with socketserver.ThreadingTCPServer(('', PORT), Proxy) as httpd:
            print('警告：降级操作具有危险性，失败导致设备损坏的风险由您自行承担！目前仅支持 OPPO Enco X / W51 降级。')
            print('请在手机上设置代理后，使用降级版欢律刷入固件。')
            print(f'固件读取完毕，固件版本号: {firminfo.group(1).decode()}，适用设备 ID: {firminfo.group(2).decode()}，设备名: {get_devicename(firminfo.group(2).decode())}.')
            print(f'已启动降级代理服务器，端口：{PORT}')
            httpd.serve_forever()
            
    except FileNotFoundError:
        print('请将 firmware.bin 放置在本目录下。')
        sys.exit(1)
