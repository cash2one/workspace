#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/18

import os
import re
import sys
import copy
import math
import random
import logging
import argparse
import requests

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
    r'Product-End-Category\.aspx\?productCategory=\d+$',  # 产品链接
    r'Product-Details\.aspx\?productId=(\d+)$',  # 详情
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
    """richardsonrfpd.com 蜘蛛"""
    name = 'richardsonrfpd'
    allowed_domains = ['www.richardsonrfpd.com']
    start_urls = ['http://www.richardsonrfpd.com/Pages/home.aspx']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback="parse_resp", follow=True),
        )
        self.headers = {
            'Host': 'www.richardsonrfpd.com',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        self.limit = 25.0

    def parse_resp(self, resp):
        if 'Product-Details' in resp.url:
            yield self.parse_detail(resp)
        elif 'productCategory=' in resp.url:
            html = resp.text.encode('utf-8')
            root = lxml.html.fromstring(html)
            # 获取页数
            search_result = root.xpath('//span[@class="SearchResult"]/text()')
            count = util.intval(search_result[0]) if search_result else 0
            pages = int(math.ceil(count / self.limit))
            if pages <= 1:
                yield None
                return
            if resp.request.meta.get('next_page', False):
                links = LinkExtractor(allow=filter_rules).extract_links(resp)
                for link in links:
                    yield Request(url=link.url, headers=self.headers, callback=self.parse_resp)
            form_data = {}
            # 获取翻页参数 post_back
            page_list = root.xpath('//tr[@class="Paging"]//a/@href')
            post_back_pattern = re.compile('\'([^\']+)\',\'([^\']+)\'')

            match = post_back_pattern.search(page_list[0]) if page_list else None
            post_data = match.group(1)

            # 获取事件参数 ctl00$scr
            match = re.search(r'(ctl00[^\"\',]+outerPanelPanel)', html)
            src = match.group() + '|' if match else ''

            # 获取事件参数 __VIEWSTATE
            field1 = root.xpath('//input[@id="__VIEWSTATE"]/@value')
            form_data['__VIEWSTATE'] = field1[0] if field1 else ''

            # 获取事件参数 __VIEWSTATEGENERATOR
            field2 = root.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')
            form_data['__VIEWSTATEGENERATOR'] = field2[0] if field2 else ''

            # 获取事件参数 __VIEWSTATEENCRYPTED 没有这个参数请求会出错
            form_data['__VIEWSTATEENCRYPTED'] = ''

            # 获取事件参数 __EVENTVALIDATION
            field3 = root.xpath('//input[@id="__EVENTVALIDATION"]/@value')
            form_data['__EVENTVALIDATION'] = field3[0] if field3 else ''

            # 构造翻页表单
            for x in xrange(2, pages):
                form_data.update({
                    'ctl00$scr': src + post_data,
                    '__EVENTTARGET': post_data,
                    '__EVENTARGUMENT': 'Page${page_num}'.format(page_num=x),
                })
                _headers = self.headers
                _headers.update({
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-MicrosoftAjax': 'Delta=true',
                    'Accept': '*/*'
                })
                yield FormRequest(url=resp.url, headers=self.headers,
                                  formdata=copy.deepcopy(form_data), meta={'next_page': True, 'page': x},
                                  callback=self.parse_resp)

    def parse_detail(self, resp):
        item = GoodsItem()
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        # goods_sn
        goods_sn_match = re.search(r'productId=(\d+)', resp.url)
        if goods_sn_match:
            item['goods_sn'] = goods_sn_match.group(1)
        else:
            logger.debug(u"解析 goods_sn 失败，重试URL:{url}".format(url=resp.url))
            return None
        # goods_name, provider_name, goods_desc
        try:
            title = root.xpath('//span[@class="ContentTitle"]')[0]
            item['goods_name'] = util.cleartext(title.text)
            provider_name = title.xpath('a')
            item['goods_desc'] = title.text_content().strip(' ')
            item['provider_name'] = util.cleartext(provider_name[0].text) if provider_name else ''
            item['provider_url'] = ''
        except IndexError:
            logger.debug(u"解析 goods_name 失败，重试URL:{url}".format(url=resp.url))
            return Request(url=resp.url, headers=self.headers)

        # goods_other_name
        goods_other_name = root.xpath('//span[@style="font-weight:bold;"]')
        for x in goods_other_name:
            match = re.search('MFG\s*Part\s*Number:\s*([^\s]+)', x.text, re.IGNORECASE)
            item['goods_other_name'] = match.group(1) if match else ''

        # url
        item['url'] = resp.url

        # catlog
        item['catlog'] = []
        catlog_div = root.xpath('//div[@class="breadcrumb"]//a')
        for catlog in catlog_div:
            catlog_name = util.cleartext(catlog.text)
            catlog_url = util.urljoin(resp.url, catlog.xpath('./@href')[0])
            if catlog_name and catlog_url:
                if '/Pages/Home.aspx' in catlog_url or 'productCategory=All' in catlog_url:
                    continue
                item['catlog'].append([catlog_name, catlog_url])

        # attr and tiered div
        div = root.xpath('//div[@id="div2"]')
        # 获取不到div就重试一次
        if not div and not resp.request.meta.get('retry'):
            logger.debug(u'网页加载不完整。重试一次 URL:{url}'.format(url=resp.url))
            return Request(url=resp.url, headers=self.headers, meta={'retry': 1})

        # rohs
        rohs_img = div[0].xpath('.//img[contains(@title, "ROHS")]/@src')
        item['rohs'] = 1 if rohs_img else -1

        # img
        img_thumb = div[0].xpath('.//table[@align="Right"]//img/@src')
        item['goods_thumb'] = util.urljoin(resp.url, img_thumb[0]) if img_thumb else ''
        img_large = div[0].xpath('.//table[@align="Right"]//a[@id="imgFull"]/@href')
        item['goods_img'] = util.urljoin(resp.url, img_large[0]) if img_large else ''

        # attr
        item['attr'] = []
        try:
            attr_table = div[0].xpath('.//td[@align="left"]//table[@class="PDTable"]//td')
            for x in range(0, len(attr_table), 2):
                attr_key = attr_table[x].text
                attr_value = attr_table[x + 1].text
                if attr_key:
                    attr_key = attr_key.strip(' ')
                    attr_value = attr_value.strip(' ') if attr_value else ''
                    if attr_value:
                        item['attr'].append([attr_key, attr_value])
                else:
                    break
        except IndexError:
            logger.debug(u"无法查找到属性列表 URL:{url}".format(url=resp.url))

        # tiered
        item['tiered'] = []
        try:
            price_table = div[0].xpath('.//td[@align="center"]//table[@class="PDTable"]/tr')
            stock = []
            for tr in price_table:
                td = tr.findall('td')
                if len(td) == 1:
                    if "Quote Required" in td[0].text:
                        item['tiered'] = [[0, 0.00]]
                        break
                    else:
                        stock.append(util.intval(td[0].text))
                elif len(td) == 2:
                    qty = util.intval(td[0].text)
                    price = util.floatval(td[1].text)
                    if price:
                        item['tiered'].append([qty, price])
                else:
                    continue
            # 可能 Manufacturer Stock 并没有显示在表格中，将其设置为0，并添加到stock中
            if len(stock) == 1:
                stock.append(0)
            # 从价格阶梯中获取最小起订量加入stock
            min_qty = item['tiered'][0][0] if item['tiered'][0][0] else 1
            stock.insert(1, min_qty)
            item['stock'] = stock
        except IndexError:
            logger.debug(u"无法正确解析价格列表 URL:{url}".format(url=resp.url))
            item['stock'] = [0, 1, 0]
            item['tiered'] = [[0, 0.00]]

        # doc
        doc_link = root.xpath('//a[@id="docDown"]/@href')
        item['doc'] = doc_link[0] if doc_link else ''

        # increment
        item['increment'] = 1

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
