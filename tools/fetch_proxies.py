#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/10

import os
import re
import sys
import argparse
import urlparse
import random
import logging
import requests
import time
import sqlite3

# scrapy import
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem, IgnoreRequest, CloseSpider
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.link import Link
from scrapy.utils.python import to_bytes

# lmxl
import lxml.html
from w3lib.html import remove_tags

sys.__APP_LOG__ = False
try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    print sys.path[0]
    import config

from tools import box

logger = logging.getLogger(__name__)

settings = {
    'BOT_NAME': 'ProxySpider',
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': True,
    'CONCURRENT_ITEMS': 100,
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_DELAY': 0.2,

    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-cn',
    },
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',

    'DOWNLOADER_MIDDLEWARES': {
        __name__ + '.IgnoreRequestMiddleware': 1,
        __name__ + '.UniqueRequestMiddleware': 3,
        __name__ + '.RandomUserAgentMiddleware': 5,

    },
    'ITEM_PIPELINES': {
        __name__ + '.MetaItemPipeline': 500,
    },
    'EXTENSIONS': {
        'scrapy.extensions.closespider.CloseSpider': 500,
    },
    'TELNETCONSOLE_ENABLED': False,
    'LOG_LEVEL': logging.DEBUG,

}
# 翻页链接规则
filter_rules = (
    # 只要前十页,十页之后的代理存活率可能很低了
    # 西刺
    'xicidaili\.com/\w{,2}/$',  # 目录
    'xicidaili\.com/\w{,2}/\d$',  # 分页
    # 开心代理
    'kxdaili\.com/dailiip/\d/\d',  # 分页
    #

)

parse_selector = {
    'www.xicidaili.com': {
        'table_header': {
            'proxy_ip': u'IP地址',
            'proxy_port': u'端口',
            'proxy_protocol': u'类型',
            'proxy_location': u'服务器地址',
        },
        'table_header_xpath': '//table[@id="ip_list"]//tr[1]/th',  # 要求解析结果为表头的list，用于定位数据具体位置
        'table_body_xpath': '//table[@id="ip_list"]//tr',  # 要求解析结果为list，即解析到表格的行
        'use_selector': True,
    },
    'www.kxdaili.com': {
        'use_selector': False,  # 简单的网站可以不使用表格的方式解析，使用正则表达式全局匹配，ip、port、protocol
        'proxy_location': None,  # 如果location可以通过正则表达式准确匹配，可以添加该字段的正则表达式
    }

}

request_list = []
total_data = 0


def headers_list_to_str(request_header):
    _headers = {}
    for k, v in request_header.iteritems():
        _headers[k] = ''.join(v)
    return _headers


class RandomUserAgentMiddleware(object):
    """随机UserAgent中间件"""

    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        if 'USER_AGENT_LIST' in crawler.settings:
            agents = crawler.settings.getlist('USER_AGENT_LIST')
        else:
            agents = config.USER_AGENT_LIST
        return cls(agents)

    def process_request(self, request, spider):
        if self.agents:
            request.headers.setdefault('User-Agent', random.choice(self.agents))


class IgnoreRequestMiddleware(object):
    """忽略请求url"""

    def __init__(self, crawler):
        global filter_rules
        self.filters = []
        for rule in filter_rules:
            self.filters.append(re.compile(rule))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        _ignore = True
        for vo in self.filters:
            if vo.search(request.url) or request.url in spider.start_urls:
                _ignore = False
                break
        if _ignore:
            raise IgnoreRequest("ignore repeat url: %s" % request.url)


class ProxyItem(scrapy.Item):
    proxy_ip = scrapy.Field()  # 代理IP
    proxy_port = scrapy.Field()  # 代理端口
    proxy_protocol = scrapy.Field()  # 代理协议
    proxy_alive = scrapy.Field()  # 代理存活标志
    proxy_fetch_date = scrapy.Field()  # 代理抓取时间
    proxy_from = scrapy.Field()  # 来源的网站域名/或者地址
    proxy_high_quality = scrapy.Field()  # 是否高品质代理
    proxy_location = scrapy.Field()  # 代理所在地区


class MetaItemPipeline(object):
    """数据集管道"""

    def __init__(self, crawler):
        name = 'spider_' + crawler.spider.name + '_item'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item, spider):
        """保存数据"""
        if not item:
            raise DropItem("item data type error")
        data = dict(item)
        if not data:
            raise DropItem("item data is empty")
        # print("=" * 10 + "process_item" + "BEGIN" + "=" * 10)
        print(data['proxy_ip'] + "  " + data['proxy_from'])
        # print("=" * 10 + "process_item" + "END" + "=" * 10)

    def close_spider(self, spider):
        pass


class ProxySpider(CrawlSpider):
    """代理 蜘蛛"""
    name = 'proxy_spider'
    allowed_domains = ['www.xicidaili.com', 'www.kxdaili.com', 'www.ip181.com', 'www.httpdaili.com', 'www.66ip.cn']
    start_urls = ['http://www.xicidaili.com/', 'http://www.kxdaili.com/dailiip.html']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(ProxySpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback="parse_selector", follow=True),
        )
        self.headers = {'Host': '',
                        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
                        'Accept-Encoding': 'gzip, deflate, sdch',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
                        'Referer': ''}
        self.guide_book = parse_selector
        self.ip_pattern = re.compile(r'>(\d+\.\d+\.\d+\.\d+)<')
        self.port_pattern = re.compile(r'>(\d+)<')
        self.protocol_pattern = re.compile(r'>(HTTPS?)<', re.IGNORECASE)

    def start_requests(self):
        for url in self.start_urls:
            host = urlparse.urlsplit(url)[1]
            self.headers.update({'Host': host})
            yield Request(url=url, headers=self.headers)

    def parse_selector(self, response):
        # 提取域名
        host = urlparse.urlsplit(response.url)[1]
        global request_list
        request_list.append(response.url)
        # 根据域名提取对应的解析xpath
        if host in self.guide_book and self.guide_book.get(host).get('use_selector', False):
            table_header = self.guide_book.get(host).get('table_header')
            table_header_xpath = self.guide_book.get(host).get('table_header_xpath')
            table_body_xpath = self.guide_book.get(host).get('table_body_xpath')
            return self.parse_detail(response, table_header=table_header,
                                     table_header_xpath=table_header_xpath,
                                     table_body_xpath=table_body_xpath)
        else:
            proxy_location = self.guide_book.get(host).get('proxy_location', None)
            return self.parse_common(response, proxy_location=proxy_location)

    def parse_detail(self, response, table_header=None, table_header_xpath=None, table_body_xpath=None):
        item = ProxyItem()
        if not (table_header and table_header_xpath and table_body_xpath):
            for item in self.parse_common(response):
                yield item
            return
        _header_list = response.xpath(table_header_xpath).extract()

        table_map = {}
        for k, v in table_header.items():
            for idx, x in enumerate(_header_list):
                if v in x:
                    table_map[k] = idx
                    break

        proxy_list = response.xpath(table_body_xpath)
        for proxy in proxy_list:
            if not proxy.xpath('.//td'):
                continue
            try:
                ip = proxy.xpath('.//td')[table_map.get('proxy_ip')]
                port = proxy.xpath('.//td')[table_map.get('proxy_port')]
                protocol = proxy.xpath('.//td')[table_map.get('proxy_protocol')]
                location = proxy.xpath('.//td')[table_map.get('proxy_location')]
            except IndexError:
                continue
            item['proxy_ip'] = ip.xpath('text()').extract().pop()
            item['proxy_port'] = port.xpath('text()').extract().pop()
            item['proxy_protocol'] = protocol.xpath('text()').extract().pop()
            item['proxy_location'] = location.xpath('text()').extract().pop()
            item['proxy_fetch_date'] = int(time.time())
            item['proxy_from'] = response.url
            item['proxy_alive'] = 1
            item['proxy_high_quality'] = 0
            yield item

    def parse_common(self, response, **kwargs):
        item = ProxyItem()
        ip_list = self.ip_pattern.findall(response.text)
        port_list = self.port_pattern.findall(response.text)
        protocol_list = self.protocol_pattern.findall(response.text)
        if kwargs.get('proxy_location', None):
            location_pattern = re.compile(kwargs.get('proxy_location'), re.UNICODE)
            location_list = location_pattern.findall(response.text)
            proxies = zip(ip_list, port_list, protocol_list, location_list)
            for ip, port, protocol, location in proxies:
                item['proxy_ip'] = ip
                item['proxy_port'] = port
                item['proxy_protocol'] = protocol
                item['proxy_location'] = location
                item['proxy_fetch_date'] = int(time.time())
                item['proxy_from'] = response.url
                item['proxy_alive'] = 1
                item['proxy_high_quality'] = 0
                yield item
        else:
            proxies = zip(ip_list, port_list, protocol_list)
            for ip, port, protocol in proxies:
                item['proxy_ip'] = ip
                item['proxy_port'] = port
                item['proxy_protocol'] = protocol
                item['proxy_location'] = ''
                item['proxy_fetch_date'] = int(time.time())
                item['proxy_from'] = response.url
                item['proxy_alive'] = 1
                item['proxy_high_quality'] = 0
                yield item

    @property
    def closed(self):
        """蜘蛛关闭清理操作"""

        def wrap(reason):
            global request_list
            global total_data
            print("=" * 10 + "close_spider" + "BEGIN" + "=" * 10)
            request_list = [urlparse.unquote(x) for x in request_list]
            print(request_list)
            print(len(request_list))
            print(total_data)
            print("=" * 10 + "close_spider" + "END" + "=" * 10)
            pass

        return wrap


def main():
    global settings
    from scrapy import cmdline
    from scrapy.settings import Settings

    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)

    act_group = parser.add_argument_group(title='操作选项组')
    act_group.add_argument('-r', '--run', dest='cmd', help='运行爬虫获取数据',
                           action='store_const', const='runspider')
    act_group.add_argument('-s', '--shell', dest='cmd', help='控制台调试',
                           action='store_const', const='shell')
    act_group.add_argument('-v', '--view', dest='cmd', help='使用浏览器打开蜘蛛获取的URL页面',
                           action='store_const', const='view')

    run_group = parser.add_argument_group(title='运行操作组')
    run_group.add_argument('-n', '--limit-num', dest='limit', default=0,
                           help='限制总请求次数，默认为0不限制', type=int)
    run_group.add_argument('-m', '--max-request-num', dest='max', default=30,
                           help='同时最大请求数，默认为30，0则不限制', type=int)
    run_group.add_argument("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                           help="设置爬虫参数（可以重复）")
    run_group.add_argument("-o", "--output", metavar="FILE",
                           help="输出 items 结果集 值FILE (使用 -o 将定向至 stdout)")
    run_group.add_argument("-t", "--output-format", metavar="FORMAT",
                           help="基于 -o 选项，使用指定格式输出 items")
    run_group.add_argument('-d', '--dist', help='分布式运行，用于其他进程提交数据',
                           action='store_true', default=False)

    gen_group = parser.add_argument_group(title='通用选择项')
    gen_group.add_argument('-u', '--url', help='设置URL，运行操作设置该项则为起始爬取URL，\
                                                                    调试操作设置则为调试URL，查看操作则为打开查看URL')

    args = parser.parse_args()
    if args.help:
        parser.print_help()
    elif args.cmd:
        settings = Settings(settings)
        if args.cmd == 'runspider':
            argv = [sys.argv[0], args.cmd, sys.argv[0]]
            for vo in run_group._group_actions:
                opt = vo.option_strings[0]
                val = args.__dict__.get(vo.dest)
                if val == vo.default:
                    continue
                if isinstance(val, (list, tuple)):
                    val = ' '.join(val)
                if vo.dest == 'limit':
                    settings['CLOSESPIDER_ITEMCOUNT'] = val
                    continue
                elif vo.dest == 'max':
                    settings['CONCURRENT_REQUESTS'] = val
                    continue
                elif vo.dest == 'dest':
                    settings['DESTRIBUT_RUN'] = val
                    continue
                argv.extend([opt, val])
            if args.url:
                argv.extend(['-a', 'START_URL=%s' % args.url])
        elif args.cmd == 'shell':
            argv = [sys.argv[0], args.cmd]
            if args.url:
                argv.append(args.url)
        elif args.cmd == 'view':
            if not args.url:
                print('please setting --url option')
                return None
            argv = [sys.argv[0], args.cmd, args.url]
        cmdline.execute(argv, settings)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()
