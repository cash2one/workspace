#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/15


import os
import re
import sys
import math
import json
import copy
import argparse
import urlparse
import random
import logging
import requests
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
    r'/shop/apac/c/[^/]+/[^/]+/$',  # 二级目录
    r'/search/resources/store/',  # 搜索链接
    r'/shop/apac/p/',  # 详情
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
    """future_electronics 蜘蛛"""
    name = 'avnet_com'
    allowed_domains = ['www.avnet.com']
    start_urls = [
        'https://www.avnet.com/shop/AllProducts?countryId=apac&catalogId=10001&langId=-1&storeId=715839038&deflangId=-1']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback="parse_resp", follow=True, process_links="print_links"),
        )
        self.headers = {
            'Host': 'www.avnet.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/57.0.2987.98 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.avnet.com/wps/portal/apac/',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'X-Requested-With': 'XMLHttpRequest',
        }

        # 判断是否是商品详情url
        self.search_url_pattern_0 = re.compile(filter_rules[0], re.IGNORECASE)
        self.search_url_pattern_1 = re.compile(filter_rules[1], re.IGNORECASE)
        self.product_url_pattern_2 = re.compile(filter_rules[2], re.IGNORECASE)

        # 每一页的商品数量
        self.limit_num = 20.0

    def print_links(self, links):
        for link in links:
            print link.url
        return links

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers=self.headers)

    def parse_resp(self, resp):
        search_page = self.search_url_pattern_0.search(resp.url)
        search_match = self.search_url_pattern_1.search(resp.url)
        product_match = self.product_url_pattern_2.search(resp.url)

        if search_page:
            soup = BeautifulSoup(resp.text.encode('utf-8'), 'lxml')
            # 页面参数
            pageId = soup.find('input', id='categoryID')
            pageId = pageId.get('value')
            # 构造查询参数
            params = {'searchType': '100',
                      'profileName': 'Avn_findProductsByCategory_Summary',
                      'searchSource': 'Q',
                      'storeId': None,
                      'catalogId': None,
                      'langId': '-1',
                      'responseFormat': 'json',
                      'pageSize': '20',
                      'pageNumber': '1',
                      '_wcf.search.internal.boostquery': 'price_USD:{0.00001+TO+*}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075',
                      'wt': 'json', }
            hidden_form = soup.find('form', id='avnsearchBox')
            catalogId = hidden_form.find('input', attrs={'name': 'catalogId'})
            storeId = hidden_form.find('input', attrs={'name': 'storeId'})
            params['storeId'] = storeId.get('value') if storeId else ''
            params['catalogId'] = catalogId.get('value') if catalogId else ''
            # 查询url
            search_url = urlparse.urljoin(resp.url, '/search/resources/store/{storeId}/'
                                                    'productview/byCategory/{pageId}'.format(storeId=params.get('storeId'), pageId=pageId)) + '?'
            for k, v in params.items():
                search_url += k + "=" + v + '&'
            else:
                search_url = search_url[:-1]
            yield Request(url=search_url, headers=self.headers, callback=self.parse_resp)
        elif search_match:
            search_dict = json.loads(resp.text.encode('utf-8'))
            count = search_dict.get('recordSetTotal', 0)
            page_num = int(math.ceil(count / 20.0))
            if page_num <= 1:
                yield self.parse_search(resp)
            for x in xrange(2, page_num + 1):
                page_url = resp.url.replace('pageNumber=1', 'pageNumber={page}'.format(page=x))
                yield Request(url=page_url, headers=self.headers, callback=self.parse_search)
        elif product_match:
            yield self.parse_detail(resp)

    def parse_search(self, resp):
        search_dict = {}
        try:
            search_dict = json.loads(resp.text.encode('utf-8'))
        except TypeError:
            logger.debug(u"无法解析搜索返回的数据。URL:{url}".format(url=resp.url))
        product_list = search_dict.get('catalogEntryView', [])
        for product in product_list:
            base_url = 'https://www.avnet.com/shop/apac/'
            product_url = product.get('avn_pdp_seo_path', '')
            product_detail = urlparse.urljoin(base_url, product_url)
            yield Request(url=product_detail, headers=self.headers, callback=self.parse_resp)

    def parse_detail(self, resp):
        """解析系列型号数据"""
        item = GoodsItem()
        try:
            soup = BeautifulSoup(resp.text, 'lxml')
            if soup is None:
                logger.debug('初始化商品详情页面失败 URL: %s', resp.url)
                return -404
        except Exception as e:
            logger.debug('初始化商品详情页面失败 URL: %s ERROR: %s', (resp.url, str(e)))
            return -404
        # goods_sn
        url_path_list = resp.url.split('/')
        goods_sn_pattern = re.compile(r'\d{19}')
        for path in url_path_list[::-1]:
            goods_sn = goods_sn_pattern.findall(path)
            if goods_sn:
                item['goods_sn'] = goods_sn[0]
                break
        if not item.get('goods_sn', False):
            logger.debug("无法从链接中解析goods_sn URL: {url} ".format(url=resp.url))
            return -400
        # goods_name
        goods_info_div = soup.find('div', class_='section-left')
        item['goods_name'] = goods_info_div.find('h1').get_text(strip=True) if goods_info_div else ''
        if not item.get('goods_name', False):
            logger.debug("无法从页面中解析goods_name URL: {url} ".format(url=resp.url))
            return -400
        # url
        item['url'] = resp.url
        # goods_img
        img_div = soup.find('div', id="outer-div1")
        img = img_div.find('img') if img_div else None
        item['goods_img'] = urlparse.urljoin(resp.url, img.get('src')) if img else ''
        # goods_thumb
        item['goods_thumb'] = item['goods_img']
        # desc
        desc_p = soup.find('p', class_='RB-pdp_short_Desc')
        item['goods_desc'] = desc_p.get_text(strip=True) if desc_p else ''
        # provider_name
        item['provider_name'] = "AVNET"
        # provider_url
        item['provider_url'] = ''
        # attr: [[None, None]]
        attr_body = soup.find('div', id="techAttr")
        attr_div = attr_body.find_all('div', class_='pdpDescriptionsBodyContent') if attr_body else []
        attr = []
        if attr_div:
            for content in attr_div:
                att_name = content.find('div', class_='pdpDescriptionColumn')
                attr_value = content.find('div', class_='pdpValueColumn')
                if att_name and attr_value:
                    attr.append([att_name.get_text(strip=True), attr_value.get_text(strip=True)])
                else:
                    continue
            item['attr'] = attr
        else:
            item['attr'] = attr
        # tiered: [[0, 0.00]]
        tiered_span = soup.find_all('span', class_='usdpart1')
        tiered = []
        if tiered_span:
            for span in tiered_span:
                qty_span = span.find('span', class_='pdpTierMinQty')
                qty = qty_span.get_text(strip=True) if qty_span else 0
                price_p = span.find('p')
                price = price_p.get_text(strip=True) if price_p else 0.00
                if qty and price:
                    tiered.append([util.intval(qty), util.floatval(price)])
                else:
                    tiered = [[0, 0.00]]
                    break
            item['tiered'] = tiered
        else:
            item['tiered'] = [[0, 0.00]]

        # stock: [0, 1]  >> [stock, qty]
        stock_input = soup.find('input', id='inStock')
        stock = stock_input.get('value') if stock_input else 0
        stock = util.intval(stock)
        # qty
        min_qty_input = soup.find('input', attrs={'name': 'min'})
        min_qty = min_qty_input.get('value') if min_qty_input else 1
        min_qty = util.intval(min_qty)
        item['stock'] = [stock, min_qty] if stock else ['0', '1']
        # increment: 1
        multi_input = soup.find('input', attrs={'name': 'mult'})
        item['increment'] = util.intval(multi_input.get('value')) if multi_input else 1
        # doc
        doc_div = soup.find('div', class_='pdfcontent')
        if doc_div is not None:
            doc_url = doc_div.find('a', class_='datasheet_align')
            item['doc'] = doc_url.get('href') if doc_url else ''
        else:
            item['doc'] = ''
        # rohs: -1
        rohs_div = soup.find('div', class_='leafcontent')
        item['rohs'] = 1 if rohs_div else -1
        # catlog: [[name, url]]
        nav = soup.find('nav', class_='breadcrumb')
        nav_ul = nav.find('ul', class_='nav') if nav else None
        catlog = []
        if nav is not None:
            lis = nav.find_all('a')
            for a in lis:
                cat_name = a.get_text(strip=True)
                cat_url = urlparse.urljoin(resp.url, a.get('href'))
                if cat_name and cat_url:
                    catlog.append([cat_name, cat_url])
                else:
                    continue
            item['catlog'] = catlog
        else:
            item['catlog'] = catlog
        # goods_other_name
        item['goods_other_name'] = ''
        # product_id
        # family_sn
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
