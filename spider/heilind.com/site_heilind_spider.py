#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import argparse
import urlparse
import random
import logging
import requests
import copy
from string import ascii_lowercase, digits
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

from tools import box as util

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
    r'estore.heilind.com/[^/]+/[^\.]+.html',
    r'estore.heilind.com/search.asp?p=[\w\d]+&mfg=&md=\d+&n=\d+',
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


class HQChipSpider(scrapy.Spider):
    """heilind 蜘蛛"""
    name = 'heilind'
    allowed_domains = ['estore.heilind.com']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.headers = {
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
            'Host': 'estore.heilind.com',
        }

    def start_requests(self):
        search_str = ascii_lowercase + digits
        search_str = 'a'
        for x in search_str:
            for y in search_str:
                url = 'https://estore.heilind.com/search.asp?p={search}&mfg=&md=2&n=25'.format(search=x + y)
                yield Request(url=url, headers=self.headers,callback=self.parse_resp)

    def parse_resp(self, resp):
        next_button = resp.xpath('//input[@value="Next"]')
        previous_button = resp.xpath('//input[@value="Previous"]')
        if 'pg' not in resp.url:
            current = 1
            url = resp.url + '&pg={current_page}&page=Next'.format(current_page=current)
            yield Request(url=url, headers=self.headers, meta={'next_page': current + 1}, callback=self.parse_resp)

        if next_button and previous_button:
            current = resp.request.meta.get('next_page')
            url = re.sub(r'pg=\d+', 'pg={current_page}'.format(current_page=current), resp.url)
            yield Request(url=url, headers=self.headers, meta={'next_page': current + 1}, callback=self.parse_resp)

        links = LinkExtractor(allow=filter_rules[0]).extract_links(resp)
        for link in links:
            yield Request(url=link.url, headers=self.headers, callback=self.parse_detail)

    def parse_detail(self, resp):
        """解析系列型号数据"""
        item = GoodsItem()
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        item.update({
            'goods_img': '',
            'goods_thumb': '',
            'provider_url': '',
            'attr': [],
            'catlog': [],
            'rohs': -1,
        })
        _table = root.xpath('//table[@class="partdetail"]')
        select_parse_mode = len(_table)
        flag = 'Product Change Notice' in resp.text.encode('utf-8')
        if select_parse_mode == 1 or flag:
            detail_table = _table[0]
            info_table = detail_table.xpath('//table[@id="partinfo"]')
            goods_sn = info_table[0].xpath('.//td[@class="txtleft"]/h4/text()') if info_table else None
            if not goods_sn:
                return
            item['goods_sn'] = goods_sn[0].strip()
            item['goods_name'] = item['goods_sn']

            # goods_other_name
            goods_other_name = info_table[0].xpath('.//tr[2]/td[2]/text()')
            item['goods_other_name'] = goods_other_name[0].strip() if goods_other_name else ''

            # provider_name
            provider_name = info_table[0].xpath('.//tr[3]/td[2]/text()')
            item['provider_name'] = provider_name[0].strip() if provider_name else ''

            # goods_desc
            goods_desc = info_table[0].xpath('.//tr[4]/td[2]/text()')
            item['goods_desc'] = goods_desc[0].strip() if goods_desc else ''

            # doc
            doc = info_table[0].xpath('.//tr[5]//h4/a/@href')
            item['doc'] = urlparse.urljoin(resp.url, doc[0]) if doc else ''

            # url
            item['url'] = resp.url

            # increment
            item['increment'] = 1

            # tiered
            price_table = detail_table.xpath('.//table[@class="price-break"]')
            if not price_table:
                item['tiered'] = [[0, 0.00]]
            else:
                tiered = []
                price_tr = price_table[0].findall('tr')
                for tr in price_tr:
                    tds = tr.findall('td')
                    qty = util.intval(tds[0].text)
                    price = util.floatval(tds[1].text, places=5)
                    if price == 0 or qty == 0:
                        break
                    tiered.append([qty, price])
                item['tiered'] = tiered if tiered else [[0, 0.00]]

            # stock
            item['stock'] = [0, 1]
            available = detail_table.xpath('./tr[2]/td[2]/text()')
            stock = util.intval(available[0].strip()) if available else 0
            # qty
            quantity = detail_table.xpath('./tr[2]/td[4]')
            input_box = quantity[0].findall('input') if quantity else None
            if input_box:
                quantity = quantity[0].xpath('//input[@class="textbox"]/@value')
            else:
                quantity = util.intval(quantity[0].text) if quantity else 1
            item['stock'] = [stock, quantity]
        elif select_parse_mode == 2:
            stock_table = _table[0].xpath('./tr[2]/td')
            info_table = _table[1]
            goods_sn = stock_table[0].text_content()
            item['goods_sn'] = goods_sn.strip()
            if not goods_sn:
                return
            item['goods_sn'] = goods_sn.strip()
            item['goods_name'] = item['goods_sn']

            # url
            item['url'] = resp.url

            # tiered
            price_table = stock_table[5].xpath('.//table[@class="price-break"]')
            if not price_table:
                item['tiered'] = [[0, 0.00]]
            else:
                tiered = []
                price_tr = price_table[0].findall('tr')
                for tr in price_tr:
                    tds = tr.findall('td')
                    qty = util.intval(tds[0].text)
                    price = util.floatval(tds[1].text, places=5)
                    if price == 0 or qty == 0:
                        break
                    tiered.append([qty, price])
                item['tiered'] = tiered if tiered else [[0, 0.00]]

            # stock
            item['stock'] = [0, 1]
            available = stock_table[1].text_content()
            stock = util.intval(available) if available.strip() else 0
            # qty
            quantity = stock_table[6]
            input_box = quantity.findall('input') if quantity is not None else None
            if input_box:
                input_value = quantity.xpath('//input[@class="textbox"]/@value')
                quantity = util.intval(input_value[0]) if len(input_value) else 1
            else:
                quantity = item['tiered'][0][0] if item['tiered'][0][0] != 0 else 1
            item['stock'] = [stock, quantity]

            # increment
            increment = stock_table[4].text_content()
            item['increment'] = util.intval(increment, index=999)

            # goods_other_name
            goods_other_name = info_table.xpath('./tr[3]/td[2]/text()')
            item['goods_other_name'] = goods_other_name[0].strip() if len(goods_other_name) else ''

            # provider_name
            provider_name = info_table.xpath('./tr[4]/td[2]/text()')
            item['provider_name'] = provider_name[0].strip() if provider_name else ''

            # goods_desc
            goods_desc = info_table.xpath('./tr[5]/td[2]/text()')
            item['goods_desc'] = goods_desc[0].strip() if goods_desc else ''

            # doc
            doc = info_table.xpath('./tr[7]//a/@href')
            item['doc'] = urlparse.urljoin(resp.url, doc[0]) if doc else ''

            # rohs
            rohs = info_table.xpath('./tr[8]//img')
            item['rohs'] = 1 if len(rohs) else -1

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
