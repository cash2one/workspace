# -*- coding: utf-8 -*-

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
    r'/products/[^/]+',  # index page
    r'/parametric/[^/]+$',  #
    r'/product/([^/]+)$',  # detail
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
    family_sn = scrapy.Field()


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


class HQChipSpider(CrawlSpider):
    """linear 蜘蛛"""
    name = 'linear'
    allowed_domains = ['shopping.netsuite.com', 'www.linear.com.cn']
    start_urls = ['http://www.linear.com.cn/products/']

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
            'Host': 'www.linear.com.cn',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        # family_sn
        self.family_sn_pattern = re.compile(r'/product/([^/]+)$', re.IGNORECASE)
        self.product_list_pattern = re.compile(r'var\s*prin=\s*(\[[^;]+\]);')
        # 库存查询正则表达式
        self.stock_pattern = re.compile(r'Quantity\s*Available\s*(\d+)', re.IGNORECASE)
        self.goods_sn_pattern = re.compile(r'/id\.(\d+)/')

    def parse_resp(self, resp):
        if '/parametric/' in resp.url:
            product_list = self.product_list_pattern.search(resp.text.encode('utf-8'))
            product_list = json.loads(product_list.group(1)) if product_list else []
            for product in product_list:
                try:
                    family_sn = product[6]
                    product_url = 'http://www.linear.com.cn/product/{family_sn}'.format(family_sn=family_sn)
                    # print resp.url
                    # print goods_name, product_url
                except IndexError:
                    logger.debug("无法解析产品详情链接。URL:{url}".format(url=resp.url))
                    break
                yield Request(url=product_url, headers=self.headers)
        elif '/product/' in resp.url:
            match = self.family_sn_pattern.search(resp.url)
            family_sn = match.group(1) if match else ''
            yield self.parse_family(resp, family_sn=family_sn)

    def parse_family(self, resp, **kwargs):
        data = {}
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        # family_sn
        # family_sn = resp.request.meta.get('family_sn', None)
        family_sn = kwargs.get('family_sn')
        if not family_sn:
            return None
        data['family_sn'] = family_sn

        # catlog
        breadcrumb = root.xpath('//p[@class="breadcrumb"]/a')
        data['catlog'] = []
        for catlog in breadcrumb:
            catlog_name = util.cleartext(catlog.text_content())
            catlog_url = catlog.xpath('./@href')[0]
            if catlog_name and catlog_url:
                data['catlog'].append([catlog_name, catlog_url])
            else:
                data['catlog'] = []
                break
        else:
            data['catlog'].append([family_sn, resp.url])
        # doc
        doc = root.xpath('//a[@class="doclink"]//@title')
        data['doc'] = "http://cds.linear.com/docs/en/datasheet/{title}".format(title=doc[0]) if doc else ''

        # get series
        search_url = 'http://shopping.netsuite.com/s.nl?' \
                     'ext=F&c=402442&sc=2&category=&search={search}'.format(search=family_sn)
        headers = copy.copy(self.headers)
        headers.update({'Host': 'shopping.netsuite.com', 'Referer': '',})
        return Request(url=search_url, headers=headers, meta={'data': copy.deepcopy(data)}, callback=self.parse_stock)

    def parse_stock(self, resp):
        root = lxml.html.fromstring(resp.text.encode('utf-8'))
        product_list = root.xpath('//tr[@valign="top"][@height=85]')
        data = resp.request.meta.get('data', {})
        for product in product_list:
            detail = product.xpath('.//a[@class="lnk12b-blackOff"]')
            # goods_name
            goods_name = detail[0].text_content() if detail else ''
            detail_url = util.urljoin(resp.url, detail[0].xpath('./@href')[0]) if detail else ''
            # goods_sn
            goods_sn = self.goods_sn_pattern.search(detail_url)
            goods_sn = goods_sn.group(1) if goods_sn else ''
            # stock
            stock = self.stock_pattern.search(util.cleartext(remove_tags(product.text_content())))
            stock = util.intval(stock.group(1)) if stock else 0
            headers = copy.copy(self.headers)
            headers.update({'Host': 'shopping.netsuite.com', 'Referer': '', })
            if goods_name and goods_sn:
                data['goods_name'] = goods_name
                data['goods_sn'] = goods_sn
                yield Request(url=detail_url, headers=headers, meta={'item': copy.deepcopy(data), 'stock': copy.deepcopy(stock)},
                              callback=self.parse_detail)
            else:
                yield Request(url=resp.url, headers=headers)
            # 翻页
            if 'range=' not in resp.url:
                links = LinkExtractor(allow=r'search=').extract_links(resp)
                for link in links:
                    yield Request(url=link.url, headers=headers,
                                  meta={'data': copy.deepcopy(data), 'stock': copy.deepcopy(stock)},
                                  callback=self.parse_stock)


    def parse_detail(self, resp):
        item = resp.request.meta.get('item', None)
        if item:
            root = lxml.html.fromstring(resp.text.encode('utf-8'))
            goods_desc = root.xpath('//td[@class="txt11"]/text()')
            item['goods_desc'] = goods_desc[0].replace('\n', '').replace('\t', '') if goods_desc else ''
            # tiered
            tiered = []
            price_list = root.xpath('//td[@class="texttable"]')
            for x in range(0, len(price_list), 2):
                qty = util.intval(price_list[x].text_content())
                price = util.floatval(price_list[x+1].text_content())
                if qty and price:
                    tiered.append([qty, price])
                else:
                    tiered = [[0, 0.00]]
                    break
            if not tiered:
                price = root.xpath('//td[@class="txt18b-red"]/text()')
                price = util.floatval(price[0]) if price else 0
                if price:
                    tiered = [1, price]
                else:
                    tiered = []

            item['tiered'] = tiered if tiered else [[0, 0.00]]
            # stock
            qty = root.xpath('//input[@id="qty"]/@value')
            qty = util.intval(qty[0]) if qty else 1
            stock = resp.request.meta.get('stock')
            item['stock'] = [stock, qty]
            # url
            item['url'] = resp.url
            # provider_name
            item['provider_name'] = 'LINEAR'
            item['provider_url'] = ''
            # attr
            item['attr'] = []
            # rohs
            item['rohs'] = -1
            item['goods_other_name'] = ''
            # increment
            item['increment'] = 1
            # img
            item['goods_img'] = ''
            item['goods_thumb'] = ''
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
