#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/5

"""
使用说明

# 设置重试次数
# Retry many times since proxies often fail
RETRY_TIMES = 10
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# 代理模式
PROXY_MODE = 0/1/2/3
0 - 从文件中读取代理列表，代理格式应符合正则表达式 (\w+://)(\w+:\w+@)?(.+)
    settings参数 PROXY_FILE = 'xxx.txt'
1 - 仅使用文件列表中的一个代理，除非代理失效
    settings参数 PROXY_FILE = 'xxx.txt'
2 - 自定义代理, 可以是代理列表或者是单独的代理字符串，代理格式应符合 (\w+://)(\w+:\w+@)?(.+)
    settings参数 CUSTOM_PROXY = "http://127.0.0.1:1080" | ['...', '...']
3 - 从代理数据库中读取代理
    settings参数 PROXY_DB = "sqlite.db"


# 依次启用重试中间件， 随机代理中间件，scrapy内置的代理中间件 
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy_proxies.RandomProxy': 100,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}
"""

import re
import random
import base64
import logging
# custom
import tools.db

log = logging.getLogger('scrapy.proxies')


class Mode:
    RANDOMIZE_PROXY_FROM_FILE, RANDOMIZE_PROXY_ONCE, SET_CUSTOM_PROXY, RANDOMIZE_PROXY_FROM_DB = range(4)

    def __init__(self):
        pass


class RandomProxy(object):
    def __init__(self, settings):
        self.mode = settings.get('PROXY_MODE')
        self.proxy_file = settings.get('PROXY_FILE')
        self.proxy_db = settings.get('PROXY_DB')
        self.chosen_proxy = ''
        if self.proxy_file is None and self.proxy_db is None and self.mode != Mode.SET_CUSTOM_PROXY:
            raise KeyError('PROXY_LIST or PROXY_DB setting is missing')

        if self.mode == Mode.RANDOMIZE_PROXY_FROM_FILE or self.mode == Mode.RANDOMIZE_PROXY_ONCE:
            fin = open(self.proxy_file)
            self.proxies = {}
            for line in fin.readlines():
                parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line.strip())
                if not parts:
                    continue

                # Cut trailing @
                if parts.group(2):
                    user_pass = parts.group(2)[:-1]
                else:
                    user_pass = -1

                self.proxies[parts.group(1) + parts.group(3)] = user_pass
            fin.close()
            if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
                self.chosen_proxy = random.choice(list(self.proxies.keys()))
        elif self.mode == Mode.RANDOMIZE_PROXY_FROM_DB:
            self.proxy_db_handle = tools.db.SQLite(database=self.proxy_db)
            self.proxies = {}
        elif self.mode == Mode.SET_CUSTOM_PROXY:
            custom_proxy = settings.get('CUSTOM_PROXY')
            self.proxies = {}
            if isinstance(custom_proxy, (unicode, str)):
                parts = re.match('(\w+://)(\w+:\w+@)?(.+)', custom_proxy.strip())
            elif isinstance(custom_proxy, (list, tuple)):
                parts = re.match('(\w+://)(\w+:\w+@)?(.+)', random.choice(custom_proxy))
            else:
                parts = None

            if not parts:
                raise ValueError('CUSTOM_PROXY is not well formatted')

            if parts.group(2):
                user_pass = parts.group(2)[:-1]
            else:
                user_pass = -1

            self.proxies[parts.group(1) + parts.group(3)] = user_pass
            self.chosen_proxy = parts.group(1) + parts.group(3)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # Don't overwrite with a random one (server-side state for IP)
        if 'proxy' in request.meta:
            if request.meta["exception"] is False:
                return
        request.meta["exception"] = False
        if len(self.proxies) == 0 and self.mode != Mode.RANDOMIZE_PROXY_FROM_DB:
            raise ValueError('All proxies are unusable, cannot proceed')

        if self.mode == Mode.RANDOMIZE_PROXY_FROM_DB:
            self.random_proxies()
            proxy_address = random.choice(list(self.proxies.keys()))
            proxy_user_pass = -1
        elif self.mode == Mode.RANDOMIZE_PROXY_FROM_FILE:
            proxy_address = random.choice(list(self.proxies.keys()))
            proxy_user_pass = self.proxies[proxy_address]
        else:
            proxy_address = self.chosen_proxy
            proxy_user_pass = self.proxies[proxy_address]

        # -1 表示无需用户名和密码认证
        if proxy_user_pass == -1:
            request.meta['proxy'] = proxy_address
        elif isinstance(proxy_user_pass, (unicode, str)):
            if proxy_user_pass:
                request.meta['proxy'] = proxy_address
                basic_auth = 'Basic ' + base64.b64encode(proxy_user_pass.encode()).decode()
                request.headers['Proxy-Authorization'] = basic_auth
            else:
                log.debug('Proxy user pass not found')
        log.debug('Using proxy <%s>, %d proxies left' % (
            proxy_address, len(self.proxies)))

    def random_proxies(self):
        if len(self.proxies) < 10:
            count = self.proxy_db_handle.get_count(table='alive')
            random_num = random.randint(1, int(count) - 100)
            proxies_list = self.proxy_db_handle.get_list(
                table='alive',
                condition={'id': {'gt': random_num}},
                limit=100,
                fields=('proxy_ip', 'proxy_port', 'proxy_protocol', 'id'),
            )
            for proxy in proxies_list:
                proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[0], port=proxy[1], protocol=proxy[2])
                proxy_id = proxy[3]
                self.proxies[proxy_url] = proxy_id

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return
        if self.mode == Mode.RANDOMIZE_PROXY_FROM_FILE or self.mode == Mode.RANDOMIZE_PROXY_ONCE or self.mode == Mode.RANDOMIZE_PROXY_FROM_DB:
            proxy = request.meta['proxy']
            if self.mode == Mode.RANDOMIZE_PROXY_FROM_DB:
                self.proxy_db_handle.delete(table='alive', condition={'id': self.proxies[proxy]})
            try:
                del self.proxies[proxy]
            except KeyError:
                pass
            request.meta["exception"] = True
            if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
                self.chosen_proxy = random.choice(list(self.proxies.keys()))
            log.info('Removing failed proxy <%s>, %d proxies left' % (
                proxy, len(self.proxies)))
