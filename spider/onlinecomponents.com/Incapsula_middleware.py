#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/9

import os
import re
import sys
import argparse
import urlparse
import random
import logging
import requests
import hashlib
import json
import copy
import time
import math
from bs4 import BeautifulSoup
# scrapy import
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem, IgnoreRequest, CloseSpider
# from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.utils.python import to_bytes
# lmxl
import lxml.html
from w3lib.html import remove_tags

sys.__APP_LOG__ = False
try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.dirname(os.path.split(os.path.realpath(__file__))[0]))
    print sys.path[0]
    import config

from tools import box

logger = logging.getLogger(__name__)

settings = {
    'BOT_NAME': 'hqchipSpider',
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
        # __name__ + '.IgnoreRquestMiddleware': 1,
        # __name__ + '.UniqueRequestMiddleware': 3,
        __name__ + '.RandomUserAgentMiddleware': 5,
        # __name__ + '.RequestsDownloader': 8,
        "tools.incapsula_cracker.IncapsulaMiddleware": 8,

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
# 过滤规则
filter_rules = (
    r'/ProductSearch/',
    r'/ParametricSearch/',
    r'http://cn\.onlinecomponents\.com/.*\.html\?p=\d+',
)

request_list = []
total_data = 0


class RequestsDownloader(object):
    def __init__(self):
        self.session = requests.Session()

    def headers_list_to_str(self, request_header):
        _headers = {}
        for k, v in request_header.iteritems():
            _headers[k] = ''.join(v)
        return _headers

    def process_request(self, request, spider):
        try:
            if getattr(request, 'headers', None) and getattr(request, 'cookies', None):
                headers = self.headers_list_to_str(request.headers)
                print("="*10 + "request_mid" + "BEGIN" + "="*10)
                print(request.url)
                print("="*10 + "request_mid" + "END" + "="*10)
                res = self.session.get(url=request.url, headers=headers, cookies=request.cookies)
            else:
                res = self.session.get(url=request.url, )
        except KeyboardInterrupt:
            raise
        return HtmlResponse(request.url, body=res.content, encoding='utf-8', request=request)

    def process_exception(request, exception, spider):
        return None


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


class IgnoreRquestMiddleware(object):
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
            raise IgnoreRequest("ingore repeat url: %s" % request.url)


class GoodsItem(scrapy.Item):
    goods_sn = scrapy.Field()  # 产品标识
    goods_name = scrapy.Field()  # 产品销售型号名
    url = scrapy.Field()  # URL
    goods_img = scrapy.Field()  # 产品图片
    goods_thumb = scrapy.Field()  # 缩略图
    goods_desc = scrapy.Field()  # 描述
    provider_name = scrapy.Field()  # 供应商/品牌
    provider_url = scrapy.Field()  # 供应商URL
    tiered = scrapy.Field()  # 价格阶梯
    stock = scrapy.Field()  # 库存信息，库存和最小购买量
    increment = scrapy.Field()  # 递增量
    doc = scrapy.Field()  # 文档
    attr = scrapy.Field()  # 属性
    rohs = scrapy.Field()  # rohs
    catlog = scrapy.Field()  # 分类
    goods_other_name = scrapy.Field()


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
        data = copy.deepcopy(dict(item))
        if not data:
            raise DropItem("item data is empty")
        print("=" * 10 + "process_item" + "BEGIN" + "=" * 10)
        print(data)
        print("=" * 10 + "process_item" + "END" + "=" * 10)

    def close_spider(self, spider):
        pass


class HQChipSpider(CrawlSpider):
    """onlinecomponents 蜘蛛"""
    name = 'onlinecomponents_com'
    allowed_domains = ['cn.onlinecomponents.com']
    start_urls = ['https://cn.onlinecomponents.com/productsearch/']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback="parse_resp", follow=True, process_links=self.put_links),
        )
        self.headers = {
            'Host': 'cn.onlinecomponents.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
        }
        self.limit_num = 10.0

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers=self.headers, callback=self.parse_resp)

    def put_links(self, links):
        for link in links:
            link.url = urlparse.unquote(link.url)
        # print links
        return links

    def parse_resp(self, resp):
        print "parse_resp begin" + "*" * 10
        print resp.text.encode('utf-8')
        print "parse_resp end" + "=" * 10



    def parse_detail(self, resp):
        item = GoodsItem()
        return item

    @property
    def closed(self):
        """蜘蛛关闭清理操作"""

        def wrap(reason):
            # del self.queue
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
