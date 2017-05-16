#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import db
import time
import Queue
import threading
import subprocess

PROXY_QUEUE = []
QUEUE_LOCK = threading.Lock()


def fill_proxy_queue():
    proxy_db = db.ProxyDB()
    fetch_proxies = proxy_db.get_iter(
        table='proxies',
        condition=None,
        limit=None,
        fields=('proxy_protocol', 'proxy_ip', 'proxy_port')
    )
    # global PROXY_QUEUE
    proxies = {}
    target = "https://www.baidu.com/index.html"
    # QUEUE_LOCK.acquire()
    for proxy in fetch_proxies:
        proxy_url = "{protocol}://{ip}:{port}".format(protocol=proxy[0], ip=proxy[1], port=proxy[2])
        proxies.update({
            'http': proxy_url,
            'https': proxy_url,
        })


def main():
    # sb = subprocess.call(['python', r'E:\workspace\tools\fetch_proxies.py', '-r'])
    fill_proxy_queue()


if __name__ == '__main__':
    main()
