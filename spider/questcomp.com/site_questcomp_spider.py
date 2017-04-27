# -*- coding: utf-8 -*-

"""questcomp整站数据爬虫

requirements:
    scrapy>=1.2.0
    lxml
"""

import os
import re
import sys
import argparse
import random
import logging
import hashlib
import copy
import bs4
import base64
import urllib
from bs4 import BeautifulSoup

try:
    from urllib2 import _parse_proxy
except ImportError:
    from urllib.request import _parse_proxy
# scrapy import
import scrapy
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

    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-cn',
    },
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',

    'DOWNLOADER_MIDDLEWARES': {
        __name__ + '.IgnoreRquestMiddleware': 1,
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
    '/InventoryList.aspx\?pnlist',
    '/questdetails.aspx\?pn',
)
proxy_rules = (
    '/',
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
        data['url'] = to_bytes(data['url'].split('#')[0])
        data['key'] = hashlib.md5(data['goods_sn']).hexdigest()
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
    """questcomp 蜘蛛"""
    name = 'questcomp'
    allowed_domains = ['www.questcomp.com']
    start_urls = ['http://www.questcomp.com/sitemap.aspx']
    # start_urls = ['http://www.questcomp.com/InventoryList.aspx']
    # start_urls = ['http://www.questcomp.com/questdetails.aspx?pn=2N2222A']

    def __init__(self, name=None, **kwargs):
        self._init_args(**kwargs)
        self.headers = {
            'Host': 'www.questcomp.com',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/57.0.2987.98 Safari/537.36',
            'Referer': 'http://www.questcomp.com/',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
        }
        super(HQChipSpider, self).__init__(name, **kwargs)

    def _init_args(self, **kwargs):
        start_url = kwargs.get('START_URL', '')
        if start_url:
            self.start_urls = [start_url]
        self.rules = (
            Rule(LinkExtractor(allow=filter_rules), callback='parse_resp', follow=True),
        )
        # logging.getLogger('pika').setLevel(logging.WARNING)
        # self.queue = queue.RabbitMQ(name='spider.' + self.name + '.links.02', dsn=config.AMQP_URL)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers=self.headers)

    def parse_resp(self, resp):
        pn = re.compile(r"/mfgstable.aspx\?pn=([^&>']+)", re.I)
        pn2 = re.compile(r"/InventoryItems.aspx\?pn=([^&>']+)", re.I)
        if '/questdetails.aspx' in resp.url or '/QuestDetails.aspx' in resp.url:
            for item in self.parse_detail(resp):
                yield item
        elif '/inventorylist.aspx?pnlist' in resp.url or '/InventoryList.aspx?pnlist' in resp.url:
            pn_list = pn.findall(resp.text.encode('utf-8'))
            pn_list.extend(pn2.findall(resp.text.encode('utf-8')))
            for pn in pn_list:
                detail_url = 'http://www.questcomp.com/questdetails.aspx?pn=%s' % pn
                yield Request(url=detail_url, headers=self.headers, callback=self.parse_resp)

    def get_part_stock(self, items_x_div=None):
        """items_x_div is bs4.element.Tag's object"""
        if not items_x_div.__class__ == bs4.element.Tag:
            return 0
        in_stock = items_x_div.find('div', id='rpt-available-qty')
        in_stock = util.intval(in_stock.get_text(strip=True)) if in_stock else 0
        return in_stock

    def get_part_manufacturer(self, items_x_div=None):
        """items_x_div is bs4.element.Tag's object"""
        if not items_x_div.__class__ == bs4.element.Tag:
            return ''
        manufacturer = items_x_div.find('div', id='rpt-mfg')
        manufacturer = manufacturer.get_text(strip=True) if manufacturer else ''
        return manufacturer

    def get_part_tiered(self, items_x_div=None):
        """items_x_div is bs4.element.Tag's object"""
        if not items_x_div.__class__ == bs4.element.Tag:
            return [[0, 0.0]]
        tiered = list()
        qty = items_x_div.find('div', id='rpt-range-qty').stripped_strings
        prices = items_x_div.find('div', id='rpt-range-price').stripped_strings
        for qty, price in zip(qty, prices):
            tiered.append([util.number_format(qty, places=0, index=0, smart=True), util.floatval(price)])
        if not tiered:
            tiered = [[0, 0.0]]
        return tiered

    def parse_detail(self, resp):
        """解析系列型号数据"""
        item = GoodsItem()
        soup = BeautifulSoup(resp.text.encode('utf-8'), 'lxml')
        # pattern
        pattern_goods_sn = re.compile(r'/questdetails.aspx\?pn=([^&]+)')

        # url
        item['url'] = resp.url

        # goods_sn
        goods_sn = pattern_goods_sn.search(resp.url)
        goods_sn = urllib.unquote(goods_sn.group(1)) if goods_sn else ''
        goods_div = soup.find('div', id='divPartNumber').stripped_strings
        item['goods_sn'] = list(goods_div)[0] if goods_div else goods_sn
        goods_sn = item['goods_sn']

        # goods_name, goods_other_name
        item['goods_name'] = item['goods_sn']
        item['goods_other_name'] = item['goods_sn']

        # goods_desc
        goods_desc_div = soup.find('div', id='MasterPageContent_ucProductHeader_detailsPartDescription').next_siblings
        item['goods_desc'] = list(goods_desc_div)[1].string.strip() if goods_desc_div else ''

        # goods_img, goods_thumb
        img = soup.find('div', class_='part-details-img')
        goods_img = img.img['src'] if img else ''
        item['goods_img'] = util.urljoin(resp.url, goods_img)
        if 'ImageComingSoon' in goods_img:
            item['goods_img'] = ''
        item['goods_thumb'] = item['goods_img']

        # rohs, attr, doc
        item['rohs'] = -1
        item['attr'] = []
        item['doc'] = ''

        # catlog
        item['catlog'] = []

        # increment
        item['increment'] = 1

        # initialization
        item['provider_name'] = ''
        item['provider_url'] = ''
        item['tiered'] = [[0, 0.00]]
        item['stock'] = [0, 1]
        # item0
        # manufacturers, stock, tiered
        item_0_div = soup.find('div', id='MasterPageContent_ucProductHeader_ucPartResults_rptPartResults_rptItems_0')
        if item_0_div:
            item_0_stock = self.get_part_stock(item_0_div)
            available_manufacturers_div = soup.find_all('div', class_='rpt-items flex-row instock')
            items_0_manufacturers = []
            if available_manufacturers_div:
                for mnf in available_manufacturers_div:
                    mnf_manufacturer = self.get_part_manufacturer(mnf)
                    mnf_stock = self.get_part_stock(mnf)
                    items_0_manufacturers.append([mnf_manufacturer, mnf_stock])
            items_0_tiered = self.get_part_tiered(item_0_div)
            for mnf in items_0_manufacturers:
                item['goods_sn'] = goods_sn
                item['provider_name'] = mnf[0]
                item['goods_sn'] = item['goods_sn'] + item['provider_name']
                item['tiered'] = items_0_tiered
                qty = item['tiered'][0][0]
                stock = mnf[1]
                if stock == 0:
                    qty = 1
                item['stock'] = [stock, qty]
                yield item
        else:
            yield item
        # items_1 to the end
        part_grid = soup.find('div', id='part-grid')
        # print part_grid
        items_0_to_end = part_grid.find_all('div', class_='rpt-items flex-row')
        if items_0_to_end:
            # print rptItems_1_to_end
            for rptItem in items_0_to_end:
                item['goods_sn'] = goods_sn
                item_stock = self.get_part_stock(rptItem)
                item_manufacturer = self.get_part_manufacturer(rptItem)
                if 'Any Manufacturer' in item_manufacturer:
                    continue
                item_tiered = self.get_part_tiered(rptItem)
                item['provider_name'] = item_manufacturer
                item['goods_sn'] = item['goods_sn'] + item['provider_name']
                item['tiered'] = item_tiered
                qty = item['tiered'][0][0]
                if item_stock == 0:
                    qty = 1
                item['stock'] = [item_stock, qty]
                yield item
        else:
            yield item

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
