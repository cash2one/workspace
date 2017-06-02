#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/2

import sys
import random
import os.path

try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    import config

import tools.db


class ProxyMiddleware(object):
    def __init__(self):
        self.proxy_file_path = os.path.join(config.APP_ROOT, 'db', 'alive.text')
        if not os.path.exists(self.proxy_file_path):
            self.proxy_file_path = None
            db_path = config.DB.get('alive', None)
            self.proxy_db = tools.db.SQLite(database=db_path) if db_path else None

    def process_request(self, request, spider):
        with_proxy_request = request.copy()
        proxy = self.random_proxies()
        with_proxy_request.meta = {"http_proxy": proxy, "https_proxy": proxy}
        with_proxy_request.dont_filter = True
        return with_proxy_request

    def random_proxies(self):
        if self.proxy_file_path:
            with open(self.proxy_file_path, 'r') as fp:
                proxies_list = [x.strip() for x in fp.readlines()]
            return random.choice(proxies_list)
        elif self.proxy_db:
            count = self.proxy_db.get_count(table='alive')
            random_num = random.randint(1, int(count) - 100)
            proxies_list = self.proxy_db.get_list(
                table='proxies',
                condition={'id': {'gt': random_num}},
                limit=100,
                fields=('proxy_ip', 'proxy_port', 'proxy_protocol', 'proxy_support_https'),
            )
            proxy = random.choice(proxies_list)
            proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[0], port=proxy[1], protocol=proxy[2])
            return proxy_url


if __name__ == '__main__':
    pass
