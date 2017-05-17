#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/17

import os
import re
import sys
import json
import argparse
import urlparse
import random
import logging
import requests
import copy

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
        # __name__ + '.IgnoreRequestMiddleware': 1,
        # __name__ + '.UniqueRequestMiddleware': 3,
        __name__ + '.RandomUserAgentMiddleware': 5,
        # __name__ + '.RequestsDownloader': 8,

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
    r'/products/[^/]+',  # index page
    r'/parametric/',  #
)

request_list = []
total_data = 0


def headers_list_to_str(request_header):
    _headers = {}
    for k, v in request_header.iteritems():
        _headers[k] = ''.join(v)
    return _headers


class RequestsDownloader(object):
    def __init__(self):
        self.session = requests.Session()

    def process_request(self, request, spider):
        try:
            if getattr(request, 'headers', None) and getattr(request, 'cookies', None):
                headers = headers_list_to_str(request.headers)
                res = self.session.get(url=request.url, headers=headers, cookies=request.cookies)
            else:
                res = self.session.get(url=request.url, )
        except KeyboardInterrupt:
            raise
        return HtmlResponse(request.url, body=res.content, encoding='utf-8', request=request)

    @staticmethod
    def process_exception(exception, spider):
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
    """linear 蜘蛛"""
    name = 'linear'
    allowed_domains = ['www.linear.com.cn']
    start_urls = ['http://www.linear.com.cn/products/']

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
            'Host': 'www.linear.com.cn',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        self.search_pattern = re.compile(filter_rules[1], re.IGNORECASE)
        self.product_list_pattern = re.compile(r'var\s*prin=\s*(\[[^;]+\]);')

    def parse_resp(self, resp):
        search_match = self.search_pattern.search(resp.url)
        if search_match:
            product_list = self.product_list_pattern.search(resp.text.encode('utf-8'))
            product_list = json.loads(product_list.group(1)) if product_list else []
            for product in product_list:
                try:
                    goods_name = product[0]
                    product_url = 'http://www.linear.com.cn/product/{goods_name}'.format(goods_name=goods_name)
                except IndexError:
                    logger.debug("无法解析产品详情链接。URL:{url}".format(url=resp.url))
                    break
                yield Request(url=product_url, headers=self.headers, meta={'goods_name': goods_name}, callback=self.parse_detail)

    def parse_detail(self, resp):
        data = {}
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        # family_sn
        family_sn = resp.request.meta.get('goods_name', None)
        if not family_sn:
            return None
        data['family_sn'] = family_sn

        # catlog
        breadcrumb = root.xpath('//p[@class="breadcrumb"]/a')
        data['catlog'] = []
        for catlog in breadcrumb:
            catlog_name = box.clear_text(catlog.text_content())
            catlog_url = catlog.xpath('./@href')[0]
            if catlog_name and catlog_url:
                data['catlog'].append([catlog_name, catlog_url])
            else:
                data['catlog'] = []
                break
        else:
            data['catlog'] = []

        # doc
        doc = root.xpath('//a[@class="doclink"]//@title')
        data['doc'] = doc[0] if doc else ''

        # get series
        buy = root.xpath('//li[@class="buy"]/a/@href')
        buy_url = urlparse.urljoin(resp.url, buy[0]) if buy else ''
        if buy_url:
            return Request(url=buy_url, headers=self.headers, meta={'data': copy.deepcopy(data)}, callback=self.parse_redirect)
        else:
            logger.debug("无法获取购买链接。URL:{url}".format(url=resp.url))
            return None

    def parse_redirect(self, resp):
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        part_list = root.xpath('//td[@class="partnumber"]')
        for part in part_list:
            part_number = box.clear_text(part.text_content)
            search_url = 'http://shopping.netsuite.com/s.nl?ext=F&c=402442&sc=2&category=&search={part_number}'.format(part_number=part_number)
            yield Request(url=search_url, headers=self.headers, meta=resp.request.meta, callback=self.parse_stock)

    def parse_stock(self, resp):
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        product_list = root.xpath('//tr[@valign="top"][@height=85]')
        for product in product_list:
            data = {}
            detail = product.xpath('.//a[@class="lnk12b-blackOff"]')
            # goods_name
            goods_name = detail[0].text_content() if detail else ''
            detail_url = urlparse.urljoin(resp.url, detail[0].xpath('./@href')[0]) if detail else ''
            # goods_sn
            goods_sn = self.goods_sn_pattern.search(detail_url)
            goods_sn = goods_sn.group(1) if goods_sn else ''
            # stock
            stock = self.stock_pattern.search(util.cleartext(remove_tags(product_list[0].text_content())))
            stock = util.intval(stock.group(1)) if stock else 0
            if goods_name and goods_sn:
                data = {'goods_name': goods_name, 'goods_sn': goods_sn}
                yield Request(url=detail_url, headers=self.headers, meta={'item': data, 'stock': copy.copy(stock)},
                              callback=self.parse_detail)
            else:
                yield Request(url=resp.url, headers=self.headers)

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
