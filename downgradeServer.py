#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import SimpleHTTPRequestHandler
import socketserver
import json
import os

PORT = 8090
data = {
    'code': 0,
    'data': {
        'content': [{
            'name': '1_all_500_0.bin',
            #'size': firmware_size,
            'url': 'http://sdk-smarthome.nearme.com.cn/firmware.bin'
        }],
        'name': 'OPPO Enco X',
        'productId': '061410',
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
            if req_datas['productId'] == '061410':
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

def get_firmsize():
    data['data']['content'][0]['size'] = str(os.path.getsize('./firmware.bin'))

if __name__ == '__main__':
    get_firmsize()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(('', PORT), Proxy) as httpd:
        print('警告：降级操作具有危险性，失败导致设备损坏的风险由您自行承担！目前仅支持 OPPO Enco X 降级。')
        print('已启动降级代理服务器，端口：{}'.format(PORT))
        httpd.serve_forever()