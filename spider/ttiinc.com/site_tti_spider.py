# -*- coding: utf-8 -*-

"""TTI整站数据爬虫

用户获取TME型号数据

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
import base64
try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy
# scrapy import
import scrapy
import requests
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import DropItem, IgnoreRequest, CloseSpider
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.utils.python import to_bytes
# six
from six.moves.urllib.request import getproxies, proxy_bypass
from six.moves.urllib.parse import unquote
from six.moves.urllib.parse import urlunparse
from scrapy.utils.httpobj import urlparse_cached
# lmxl
import lxml.html
from w3lib.html import remove_tags

sys.__APP_LOG__ = False
try:
    import config
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    import config
import packages.Util as util
from packages import hqchip
from packages import rabbit as queue

logger = logging.getLogger(__name__)

settings = {
    'BOT_NAME': 'hqchipSpider',
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': True,
    'CONCURRENT_ITEMS': 100,
    'CONCURRENT_REQUESTS': 16,
    # 'DOWNLOAD_DELAY': 0.2,
    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-cn',
    },
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',

    'DOWNLOADER_MIDDLEWARES': {
        # __name__ + '.IgnoreRquestMiddleware': 1,
        __name__ + '.UniqueRequestMiddleware': 3,
        __name__ + '.RandomUserAgentMiddleware': 5,
        # __name__ + '.ProxyRequestMiddleware': 8,
    },
    'ITEM_PIPELINES': {
        __name__ + '.MetaItemPipeline': 500,
    },
    'EXTENSIONS': {
        'scrapy.extensions.closespider.CloseSpider': 500,
    },
    'TELNETCONSOLE_ENABLED': False,
    'LOG_LEVEL': logging.DEBUG,

    # 'SCHEDULER': "scrapy_rabbitmq.scheduler.Scheduler",
    # 'SCHEDULER_PERSIST': True,
    # 'SCHEDULER_QUEUE_CLASS': 'scrapy_rabbitmq.queue.SpiderQueue',

}
# 过滤规则
filter_rules = (
    r'/.*/part-search.html.*systemsCatalog=\d+',  # 分类
)

# # 代理规则
# proxy_rules = (
#     'https://www.ttiinc.com/bin/services/processData\?jsonPayloadAvailable=true&osgiService=partsearchpost',
# )


def fetcher(url, data=None, **kwargs):
    '''获取URL数据'''
    global _headers
    if kwargs.get('headers'):
        _headers = kwargs['headers']
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 30)
    _page = ''
    if 'page' in kwargs:
        _page = '; Page : %s' % kwargs['page']
    if not kwargs.get('hide_print', False):
        print 'Fetch URL ：%s %s' % (url, _page)
    try:
        if 'method' in kwargs:
            method = kwargs['method']
        else:
            method = 'GET' if data is None else 'POST'
        rs = requests.request(method, url, data=data, headers=_headers, cookies=cookies,
                              proxies=proxies, timeout=timeout)
    except Exception as e:
        print('请求异常 ; %s' % e)
        return None

    if rs.status_code != 200:
        print('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None

    if 'return_response' in kwargs:
        return rs
    return rs.text


def _parse_incapsula_page(text, **kwargs):
    """解析incapsula cdn验证跳转页面"""
    match = re.search('var\s+b\s*=\s*"([^"]+)', text)
    if not match:
        return None
    print('解析incapsula cdn验证跳转页面中......')
    content = match.group(1).decode('hex')
    match = re.search(',\s*"(/_Incapsula[^"]+)', content)
    if not match:
        return None
    js_cookies = kwargs.get('cookies', {})

    url = urlparse.urljoin('https://www.ttiinc.com/', match.group(1))
    if 'url' in kwargs:
        del kwargs['url']
    rs = fetcher(url, return_response=1, **kwargs)
    if not rs:
        return None
    for vo in rs.cookies:
        js_cookies[vo.name] = vo.value
    return js_cookies


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


class UniqueRequestMiddleware(object):
    """去重请求中间件"""

    def __init__(self, crawler):
        name = 'spider_' + crawler.spider.name + '_item'
        self.mongo = hqchip.db.mongo[name]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def close_spider(self, spider):
        del self.mongo

    def process_request(self, request, spider):
        url = to_bytes(request.url.split('#')[0])
        key = hashlib.md5(url).hexdigest()
        info = self.mongo.find_one({'key': key})
        if info:
            logger.warn("ingore repeat url: %s" % request.url)
            raise IgnoreRequest("ingore repeat url: %s" % request.url)


class ProxyRequestMiddleware(object):
    """代理请求中间件"""
    def __init__(self, crawler):
        global proxy_rules
        self.filters = []
        for rule in proxy_rules:
            self.filters.append(re.compile(rule))
        self.mongo = hqchip.db.mongo.proxys
        self.queue = queue.RabbitMQ(name='spider.proxys', dsn=config.AMQP_URL)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def close_spider(self, spider):
        del self.mongo
        del self.queue

    def process_request(self, request, spider):
        if not self._check_rules(request):
            return
        proxies = {}
        try:
            data = self.queue.get(block=False)
            proxies['http'] = self._get_proxy(data['ip'], 'http')
            proxies['https'] = self._get_proxy(data['ip'], 'https')
        except:
            self._fill_queue(100)
        self._set_proxy(request, proxies)

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta or not self._check_rules(request):
            return
        request.meta['retry_num'] = 0
        return request

    def _check_rules(self, request):
        _use_proxy = False
        for vo in self.filters:
            if vo.search(request.url):
                _use_proxy = True
                break
        return _use_proxy

    def _fill_queue(self, limit_num=100):
        """填充队列"""
        total_count = self.mongo.find().count()
        skip_num = random.randint(0, total_count - limit_num) if total_count > limit_num else 0
        dlist = self.mongo.find({}).skip(skip_num).limit(limit_num)
        for vo in dlist:
            self.queue.put({'ip': vo['ip'], 'anonymous': vo['anonymous']})

    def _get_proxy(self, url, orig_type):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse((proxy_type or orig_type, hostport, '', '', '', ''))
        if user:
            user_pass = to_bytes(
                '%s:%s' % (unquote(user), unquote(password)),
                encoding=self.auth_encoding)
            creds = base64.b64encode(user_pass).strip()
        else:
            creds = None
        return creds, proxy_url

    def _set_proxy(self, request, proxies):
        if not proxies:
            return
        parsed = urlparse_cached(request)
        scheme = parsed.scheme
        if scheme in ('http', 'https') and proxy_bypass(parsed.hostname):
            return
        if scheme not in proxies:
            return
        creds, proxy = proxies[scheme]
        request.meta['proxy'] = proxy
        if creds:
            request.headers['Proxy-Authorization'] = b'Basic ' + creds


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
        self.mongo = hqchip.db.mongo[name]
        self.mongo.ensure_index('key', unique=True)
        self.mongo.ensure_index('goods_sn', unique=False)

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
        data['url'] = to_bytes(item['url'].split('#')[0])
        data['key'] = hashlib.md5(data['url']).hexdigest()
        info = self.mongo.find_one({'goods_sn': data['goods_sn']})
        if not info:
            self.mongo.insert(data)
            logger.info('success insert mongodb : %s' % data['key'])
        else:
            self.mongo.update({'_id': info['_id']}, {"$set": data})
            logger.info('success update mongodb : %s' % data['key'])
        raise DropItem('success process')

    def close_spider(self, spider):
        del self.mongo


class HQChipSpider(scrapy.Spider):
    """TTI 蜘蛛"""
    name = 'tti'
    allowed_domains = ['www.ttiinc.com']
    start_urls = ['https://www.ttiinc.com/content/ttiinc/en.html']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.tti = 'https://www.ttiinc.com/'
        self.limit_num = 25.0
        self.processData_url = 'https://www.ttiinc.com/bin/services/processData?jsonPayloadAvailable=true&osgiService=partsearchpost'
        self.form_data = {"searchTerms": "", "systemsCatalog": "254428", "pageNum": "1", "inStock": "",
                          "rohsCompliant": "", "leadFree": "", "containsLead": ""}
        self.headers = {
            'Host': 'www.ttiinc.com',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.ttiinc.com/content/ttiinc/en/apps/part-search.html?manufacturers=&searchTerms=&systemsCatalog=254428',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }
        self.manufacturers = {}
        logging.getLogger('pika').setLevel(logging.WARNING)
        # self.queue = queue.RabbitMQ(name='spider.' + self.name + '.links.02', dsn=config.AMQP_URL)

    def start_requests(self):
        match = []
        url = self.start_urls[0]
        rs = requests.get(url, headers=self.headers)
        js_cookies = {}
        for vo in rs.cookies:
            js_cookies[vo.name] = vo.value
        rs = requests.get(url, headers=self.headers, cookies=js_cookies)
        js_cookies = _parse_incapsula_page(rs.text, cookies=js_cookies, headers=self.headers)
        resp = requests.get(url='https://www.ttiinc.com/content/ttiinc/en/manufacturers.html', headers=self.headers,
                            cookies=js_cookies)
        manufacturers = re.findall(r'(/content/ttiinc/en/manufacturers/.*/(.*).html)', resp.text.encode('utf-8'))
        for v, k in manufacturers:
            self.manufacturers[k] = util.urljoin(self.tti, v)
        rs = requests.get(url, headers=self.headers, cookies=js_cookies)
        match = re.findall(r'/.*/part-search.html.*systemsCatalog=(\d+)', rs.text.encode('utf-8'))
        # if not match:
        #     with open(os.path.split(os.path.realpath(__file__))[0] + r'\tti_category_values.txt', 'r') as fp:
        #         for line in fp.readlines():
        #             match.append(line.strip())
        for systems_catalog in match:
            try:
                self.form_data['systemsCatalog'] = systems_catalog
                # print '*'*50
                # print self.form_data
                yield Request(url=self.processData_url, method='POST', headers=self.headers,
                              body=json.dumps(self.form_data), meta={'systemsCatalog': systems_catalog})
            except:
                logger.exception('Request error, systemsCatalog: %s', systems_catalog)

    def parse(self, resp):
        systems_catalog = 0
        try:
            product_dict = json.loads(resp.text.encode('utf-8'))
            systems_catalog = resp.meta.get('systemsCatalog')
            total_match_count_string = util.intval(product_dict.get('totalMatchCountString'))
            pages = int(math.ceil(total_match_count_string / self.limit_num))
            for pageNum in xrange(1, pages + 1):
                self.form_data['pageNum'] = str(pageNum)
                yield Request(url=self.processData_url, method='POST', headers=self.headers,
                              body=json.dumps(self.form_data), meta={'systemsCatalog': systems_catalog},
                              callback=self.parse_detail)
        except:
            logger.exception('Parse error, systemsCatalog: %s', systems_catalog)

    def parse_detail(self, resp):
        """解析系列型号数据"""
        item = GoodsItem()
        # with open('1.html', 'w') as fp:
        #     fp.write(resp.text.encode('utf-8'))
        try:
            systems_catalog = resp.meta.get('systemsCatalog')
            product_dict = json.loads(resp.text.encode('utf-8'))
            # 获取页面产品列表
            item_list = product_dict.get('parts').get('records', [])
            for it in item_list:
                # 商品标识
                item['goods_sn'] = it.get('partsNumber', '')
                item['goods_name'] = it.get('mfrPartNumber', '')
                item['goods_other_name'] = it.get('partsNumber', '')
                # 商品描述
                item['goods_desc'] = it.get('abbreviatedPartsDescriptionHTML', '')
                # 厂商标识
                item['provider_name'] = it.get('manufacturer', '')
                item['provider_url'] = ''
                for x in item['provider_name'].split():
                    for k in self.manufacturers.keys():
                        if x.lower() in k:
                            if not item['provider_url']:
                                item['provider_url'] = self.manufacturers.get(k)
                            else:
                                break
                # 商品图片
                item['goods_img'] = it.get('prefixedLocalImageLink', '')
                item['goods_thumb'] = it.get('prefixedThumbnailLocalImageLink', '')
                # 商品文档
                item['doc'] = it.get('datasheetURL', '')
                # rohs
                item['rohs'] = 1 if it.get('roHSTTI') == 'Y' else -1
                # [库存, 最小起订量]
                item['stock'] = [0, 0]
                item['stock'] = [it.get('ttiWebAtsInt', 0), it.get('ttiSalesMinInt', 0)]
                # 增长量
                item['increment'] = it.get('ttiSalesMultInt')
                if item['stock'][0] == 0:
                    item['increment'] = 1
                # 价格阶梯
                item['tiered'] = []
                prices_list = it.get('prices', [])
                for prices in prices_list:
                    item['tiered'].append([prices.get('quantity'), util.floatval(prices.get('price'))])
                if not item['tiered']:
                    item['tiered'] = [[0, 0.00]]
                # 属性
                item['attr'] = []
                attr_dict = it.get('parametricMap', {})
                for k, v in attr_dict.items():
                    item['attr'].append([k, v])
                # 分类
                breadcrumb = product_dict.get('breadcrumbOptions').get('producttype').get('All Systems Catalog')
                item['catlog'] = []
                for vo in breadcrumb:
                    catalog_text = vo.get('displayText')
                    catalog_value = vo.get('submitValue')
                    catalog_url = util.urljoin(self.tti, '/content/ttiinc/en/apps/part-search.html?manufacturers=&amp'
                                                         ';searchTerms=&amp;systemsCatalog=%s' % (catalog_value))
                    item['catlog'].append([catalog_text, catalog_url])
                # url
                mfrShortname = it.get('mfgShortname', '')
                partsNumber = it.get('partsNumber')
                minQty = it.get('ttiSalesMin')
                product_url = '/content/ttiinc/en/apps/part-detail.html?mfrShortname=%s&partsNumber=%s&customerPartNumber=&minQty=%s&customerId=' % (
                    mfrShortname, partsNumber, minQty)
                item['url'] = util.urljoin(self.tti, product_url)
                yield item
        except:
            with open('worry.htm', 'w') as fp:
                fp.write(resp.text.encode('utf-8'))
            logger.exception('Parse error, systemsCatalog: %s', systems_catalog)

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
    # print util.number_format("""<div class="viewProdDiv">显示 1 - 20 个产品，共 815  个
    # 				</div>""", places=0, index=0, smart=True)
    # print util.urljoin("http://www.baidu.com/", "/hello/world")
    # print util.intval("hello中文")
    main()
    # print os.path.split(os.path.realpath(__file__))[0]
