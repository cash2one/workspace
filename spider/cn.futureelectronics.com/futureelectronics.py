#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/4

# -*- coding: utf-8 -*-

"""
requirements:
    scrapy>=1.2.0
    lxml
"""

import os
import re
import sys
import argparse
import urlparse
import random
import logging
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
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.utils.python import to_bytes
# lmxl
import lxml.html
from w3lib.html import remove_tags
headers_string = """
Host: cn.futureelectronics.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding: gzip, deflate, sdch
Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
"""

sys.__APP_LOG__ = False
try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.dirname(os.path.split(os.path.realpath(__file__))[0]))
    print sys.path[0]
    import config
from tools.box import headers_to_dict
default_headers = headers_to_dict(headers_string)
print default_headers

logger = logging.getLogger(__name__)

settings = {
    'BOT_NAME': 'hqchipSpider',
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': True,
    'CONCURRENT_ITEMS': 100,
    'CONCURRENT_REQUESTS': 16,

    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-cn',
    },
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',

    'DOWNLOADER_MIDDLEWARES': {
        # __name__ + '.IgnoreRquestMiddleware': 1,
        # __name__ + '.UniqueRequestMiddleware': 3,
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
# 过滤规则
filter_rules = (
    r'/search\.aspx\?dsNav=',
    r'/Technologies/.*/Product\.aspx\?ProductID=',
    r'/technologies/.*/Pages/.*\.aspx'
)


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
        print "="*20
        print data

    def close_spider(self, spider):
        pass


class HQChipSpider(CrawlSpider):
    """future_electronics 蜘蛛"""
    name = 'future_electronics'
    allowed_domains = ['cn.futureelectronics.com']
    # start_urls = ['http://cn.futureelectronics.com/zh/Pages/index.aspx']
    # start_urls = ['http://cn.futureelectronics.com/zh/Technologies/Product.aspx?ProductID=LM2904DTSTMICROELECTRONICS3063998&IM=0']
    start_urls = ['http://cn.futureelectronics.com/zh/technologies/passives/inductors/wirewound-inductors/Pages/1004195-LQW15AN15NG00D.aspx']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback='parse_resp',
                 follow=True, process_links=self.put_links),
        )
        self.headers = {'Host': 'cn.futureelectronics.com', 'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4', 'Accept-Encoding': 'gzip, deflate, sdch', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36'}
        self.cookies = {
            'SelectedCurrency': 'NY',
            'SelectedLanguage': 'zh-CN',
        }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers=self.headers, cookies=self.cookies)

    def put_links(self, links):
        links = list(set(links))
        return links

    def parse_resp(self, resp):
        # detail url
        product_url_pattern_1 = re.compile(r'/Technologies/.*/Product\.aspx\?ProductID=', re.IGNORECASE)
        product_url_pattern_2 = re.compile(r'/technologies/.*/Pages/.*\.aspx', re.IGNORECASE)
        match = product_url_pattern_1.search(resp.url) or product_url_pattern_2.search(resp.url)
        if match:
            self.parse_detail(resp)

    def parse_detail(self, resp):
        """解析系列型号数据"""
        item = GoodsItem()
        try:
            soup = BeautifulSoup(resp.text.encode('utf-8'), 'lxml')
        except:
            logger.debug(u"初始化BS4对象失败 URL:{url}".format(url=resp.url))
            # 重试一次
            return Request(url=resp.url, headers=self.headers, cookies=self.cookies)
        # goods_sn
        product_id_pattern_1 = re.compile(r'ProductID=([^&]+)', re.IGNORECASE)
        product_id_pattern_2 = re.compile(r'/Pages/(.*)\.aspx', re.IGNORECASE)
        product_id = product_id_pattern_1.search(resp.url) or product_id_pattern_2.search(resp.url)
        goods_sn = product_id.group(1) if product_id else ''
        item['goods_sn'] = goods_sn
        if not goods_sn:
            # logger.info(u"获取goods_sn失败 URL:{url}".format(url=resp.url))
            return None
        # goods_name
        product_ref = soup.find('p', class_='ref')
        goods_name = ''
        if product_ref:
            goods_name_pattern = re.compile(ur'<b>制造商零件编号:</b>\s*([^\"\'<>/]+)')
            product_ref_list = unicode(product_ref).split('<br/>')
            for x in product_ref_list:
                match = goods_name_pattern.search(x)
                if match:
                    goods_name = match.group(1)
                    break
        item['goods_name'] = goods_name
        # goods_other_name
        item['goods_other_name'] = ''
        # goods_desc
        goods_desc = soup.find('p', class_='desc')
        item['goods_desc'] = goods_desc.get_text(strip=True) if goods_desc else ''
        # provider_name and provider_url
        provider_name = soup.find('img', id='ctl00_PlaceHolderMain_mfrLogo')
        item['provider_name'] = provider_name.get('title', '')
        if not provider_name:
            desc_div = soup.find('div', id='product-desc')
            provider_name = desc_div.find('h2')
            provider_name = provider_name.get_text(strip=True) if provider_name else ''
            item['provider_name'] = provider_name
        item['provider_url'] = ''
        # url
        item['url'] = resp.url
        # doc
        doc = soup.find('a', id='ctl00_PlaceHolderMain_csDownloadCenter_linkDatasheetUrlJustText')
        item['doc'] = doc.get('href', '')
        # goods_img and goods_thumb
        goods_img = soup.find('img', id='previewedMEDImage')
        item['goods_img'] = goods_img.get('src', '')
        goods_thumb = soup.find('img', id='thumbnail-1')
        item['goods_thumb'] = goods_thumb.get('src', '')
        # catlog
        item['catlog'] = []
        catlog = soup.find('ul', id='breadcrumb-navigation')
        catlog_list = catlog.find_all('a')
        for a in catlog_list:
            breadcrumb_name = a.get_text(strip=True)
            # TODO 修改为util.urljoin
            breadcrumb_url = urlparse.urljoin(resp.url, a.get('href', ''))
            item['catlog'].append([breadcrumb_name, breadcrumb_url])
        # attr
        item['attr'] = []
        product_attr_div = soup.find('div', id='product-details-overview-highlights')
        product_attr_list = product_attr_div.find_all('li') if product_attr_div else []
        for li in product_attr_list:
            attr_name, attr_value = li.get_text(strip=True).split(':')
            item['attr'].append([attr_name, attr_value])
        # tiered
        item['tiered'] = []
        price_table = soup.find('table', class_='product-prices')
        price_tr_list = price_table.find_all('tr', class_='price-break')
        for tr in price_tr_list:
            qty_th = tr.find('th')
            # TODO qty提取第一个数值
            qty = qty_th.get_text(strip=True) if qty_th else 0
            price_span = tr.find('span')
            # TODO price转为浮点型
            price = price_span.get_text(strip=True) if price_span else 0.00
            # print qty, price
            if qty and price:
                item['tiered'].append([qty, price])
            else:
                item['tiered'] = [0, 0.00]
        # stock、increment、 min_qty
        stock_div = soup.find('div', id='product-qty-content')
        stock_tr = stock_div.find('tr', class_='qtyInStock')
        increment_tr = stock_div.find('tr', class_='multipleOf')
        min_qty_tr = stock_div.find('tr', class_='minOrderQty')
        # TODO 类型转换
        stock = stock_tr.find('td', class_='qty').get_text(strip=True) if stock_tr else 0
        increment = increment_tr.find('td', class_='qty').get_text(strip=True) if increment_tr else 1
        min_qty = min_qty_tr.find('td', class_='qty').get_text(strip=True) if min_qty_tr else 1
        item['stock'] = [stock, min_qty]
        item['increment'] = increment
        # rohs
        rohs_div = soup.find('div', id='ctl00_PlaceHolderMain_imgRoHS')
        item['rohs'] = 1 if rohs_div else -1
        return item

    @property
    def closed(self):
        """蜘蛛关闭清理操作"""

        def wrap(reason):
            # del self.queue
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
