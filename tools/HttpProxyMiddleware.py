#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/2

import sys
import random
import os.path
import logging

try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    import config

import tools.db
proxy_middleware_logger = logging.getLogger('ProxyMiddleware')


class ProxyMiddleware(object):
    def __init__(self):
        self.proxy_file_path = os.path.join(config.APP_ROOT, 'db', 'alive.txt')
        self.proxy_db_path = config.DB.get('alive_db', None)
        if os.path.exists(self.proxy_db_path):
            self.proxy_db = tools.db.SQLite(database=self.proxy_db_path) if self.proxy_db_path else None

    def process_request(self, request, spider):
        if 'proxy' in request.meta:
            if request.meta["exception"] is False:
                return
        with_proxy_request = request.copy()
        proxy = self.random_proxies()
        with_proxy_request.meta['proxy'] = proxy
        with_proxy_request.dont_filter = True
        proxy_middleware_logger.debug(u"代理地址 {URL}".format(URL=proxy))

    def random_proxies(self):
        if self.proxy_db:
            count = self.proxy_db.get_count(table='alive')
            random_num = random.randint(1, int(count) - 100)
            proxies_list = self.proxy_db.get_list(
                table='alive',
                condition={'id': {'gt': random_num}},
                limit=100,
                fields=('proxy_ip', 'proxy_port', 'proxy_protocol', 'proxy_support_https'),
            )
            proxy = random.choice(proxies_list)
            proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[0], port=proxy[1], protocol=proxy[2])
            return proxy_url
        else:
            with open(self.proxy_file_path, 'r') as fp:
                proxies_list = [x.strip() for x in fp.readlines()]
            return random.choice(proxies_list)


if __name__ == '__main__':
    pass
