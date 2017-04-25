# coding=utf-8
import sys
import os
import re
import argparse
import time
import urllib
import math
import socket
import select
import hashlib
import logging
import threading

try:
    import json
except ImportError:
    import simplejson as json

import requests
import pymongo
import pika
from bs4 import BeautifulSoup, SoupStrainer

try:
    import conf
except ImportError:
    sys.path[0] = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
    import conf

import packages.Util as util
from packages.DB import db_mysql

try:
    from serek import serialize, unserialize
except ImportError:
    from phpserialize import serialize, unserialize

data = {
    'goods_name': '产品名',  # str
    'goods_other_name': '其他名',  # str
    'goods_desc': '产品描述',  # str
    'goods_img': '产品图片',  # str
    'goods_thumb': '缩略图',  # str
    'url': '产品链接',  # str
    'tiered': '价格阶梯',  # [[qty, hk_price, cn_price, oversea_price]]
    'brand': '品牌',  # str
    'hk_stock': '香港库存',  # 0
    'cn_stock': '大陆库存',  # 0
    'increment': '增长量',  # 1
    'min_buynum': '最小购买量',  # 1
    'category': '目录'  # [str, ]
}

# 默认配置
PRICE_PROPORTION = 6.7  # 价格系数
PN2 = 'HQCHIP(site_name)'  # 供应商标识
CDT = '1-2工作日'  # 大陆交期
HDT = ''

_params = {  # 搜索参数
    'keyword': "",
}

_logger = logging.getLogger('hqchip_spider')


def get_time_desc(t):
    """
    获取时间描述
    :param t:
    :return:
    """
    _time_desc = ''
    h = int(t / 3600)
    if h >= 1:
        _time_desc += '%s 小时' % h
    m = int((t - h * 3600) / 60)
    if m >= 1:
        _time_desc += '%s 分' % m
    s = util.number_format(t - h * 3600 - m * 60, 3)
    if s >= 0:
        _time_desc += '%s 秒' % s
    return _time_desc


def str_to_unicode(text):
    """字符串转unicode字符串"""
    if not isinstance(text, str):
        return text
    return text.decode('utf-8')


def fetcher(url, data=None, **kwargs):
    """获取URL数据"""
    if kwargs.get('headers', None):
        _headers = kwargs['headers']
    else:
        _headers = {
            # 根据网站定义
        }
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 30)
    params = kwargs.get('params')
    try:
        if 'method' in kwargs:
            method = kwargs['method']
        else:
            method = 'GET' if data is None else 'POST'
        rs = requests.request(method, url, data=data, headers=_headers,
                              cookies=cookies, proxies=proxies,
                              timeout=timeout, params=params)
    except Exception as e:
        _logger.info('请求异常 ; %s' % e)
        return None

    if rs.status_code != 200 and kwargs.get('error_halt', 1):
        _logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None

    _page = ''
    if 'page' in kwargs:
        _page = '; Page : %s' % kwargs['page']
    if not kwargs.get('hide_print', False):
        print 'Fetch URL ：%s %s' % (rs.url.encode('utf-8'), _page)

    if 'return_response' in kwargs:
        return rs
    return rs.text


def _catch_mongo_error(func):
    """捕获mongo错误"""

    def wrap(self):
        try:
            return func(self)
        except (select.error, socket.error, pymongo.errors.AutoReconnect) as e:
            self.__mongo = None
            return func(self)

    return wrap


class HQChipSupplier(object):

    def __init__(self, **kwargs):
        self.total = 0
        if not self._init_args(**kwargs):
            return
        if self.action == 'clear':
            _total_num = self.clear_data()
        else:
            _total_num = self.run()
            if _total_num > 0:
                self.check_goods()
            else:
                exception_notice()
        _run_time = get_time_desc(time.time() - self._start_time)
        print('=' * 50)
        print("%s success, 共处理 %s 个数据, 本次操作共耗时：%s \n" %
              (self.action, _total_num, _run_time))

    def _init_args(self, **kwargs):
        """初始化参数"""
        self.__hqchip_queue = {}
        self.__supplier_queue = {}
        self.__mongo_queue = {}
        self.__data = {}
        self.action = kwargs['action']
        self._start_time = time.time()
        self.threadnum = kwargs.get('threadnum', 10)
        return True

    @property
    def hqchip(self):
        '''
        连接hqchip数据库
        '''
        tname = threading.current_thread().name
        if tname not in self.__hqchip_queue:
            _db_config = conf.DATABASES['mysql'][0].copy()
            _db_config['db'] = 'hqchip'
            _db_config['tablepre'] = 'ecs_'
            _db_config['db_fields_cache'] = 0
            _db_config['data_type'] = 'dict'
            self.__hqchip_queue[tname] = db_mysql(**_db_config)
        return self.__hqchip_queue[tname]

    @property
    def supplier(self):
        '''
        连接supplier数据库
        '''
        tname = threading.current_thread().name
        if tname not in self.__supplier_queue:
            _db_config = conf.DATABASES['mysql'][0].copy()
            _db_config['db'] = 'supplier'
            _db_config['tablepre'] = 'ic_'
            _db_config['db_fields_cache'] = 0
            _db_config['data_type'] = 'dict'
            self.__supplier_queue[tname] = db_mysql(**_db_config)
        return self.__supplier_queue[tname]

    @property
    @_catch_mongo_error
    def mongo(self):
        tname = threading.current_thread().name
        if tname not in self.__mongo_queue:
            conn = pymongo.MongoClient(conf.DATABASES['mongo'][1])
            self.__mongo_queue[tname] = conn.get_default_database()
        return self.__mongo_queue[tname]

    def run(self):
        """运行操作"""
        _total_num = self.process_url_goods(_params, parse_page=True)
        # 调用
        return _total_num

    def process_url_goods(self, params, dlist=None, parse_page=False):
        _total_num = 0
        return _total_num

    def import_goods(self, data, put_xs_list=None):
        """导入产品数据"""
        put_xs_list = put_xs_list if put_xs_list else []
        if not data:
            return 0
        data['category'] = [x.encode('utf-8') for x in data['category']]
        cids = self.get_ic_category(data['category'])
        try:
            cat_id1 = cids[0]
        except IndexError:
            cat_id1 = 0
        try:
            cat_id2 = cids[1]
        except IndexError:
            cat_id2 = 0
        goods_sn = data['goods_sn']
        min_buynum = data['min_buynum']
        data['mpq'] = 1
        increment = data['increment']
        url = data['url']
        goods_desc = util.binary_type(data['goods_desc']) if data['goods_desc'] else ''
        goods_img = data['goods_img'] if 'goods_img' in data else ''
        _unix_time = int(time.time())
        goods_data = {
            'cat_id1': cat_id1,
            'cat_id2': cat_id2,
            'cat_id3': 0,
            'PN2': PN2,
            'goods_name': util.binary_type(data['goods_name']),
            'goods_other_name': util.binary_type(data['goods_other_name']),
            'provider_name': util.binary_type(data['brand']),
            'batch_number': '',
            'encap': '',
            'goods_desc': goods_desc,
            'SPQ': data['mpq'],
            'goods_number_hk': data['hk_stock'] if 'hk_stock' in data else 0,
            'goods_number': data['cn_stock'] if 'cn_stock' in data else 0,
            'DT_HK': HDT,
            'DT': CDT,
            'CDT': CDT,
            'HDT': HDT,
            'increment': increment,
            'min_buynum': min_buynum,
            'goods_sn': goods_sn,
            'brand_goods_id': 0,
            'doc_url': '',
            'digikey_url': url,
            'series': '',
            'source_type': 0,
            'user_id': 0,
            'log_id': 0,
            'to_china': 1,
            'to_hongkong': 0,
            'goods_weight': 0.0,
            'goods_img': goods_img,
            'goods_thumb': goods_img,
            'last_update': _unix_time - 8 * 3600,
        }
        if goods_data['provider_name']:
            brand_id = self.get_ic_brand(goods_data['provider_name'])
            goods_data['brand_id'] = brand_id

        info = self.supplier.select('goods', condition={'goods_sn': goods_sn, 'PN2': PN2},
                                    fields=('goods_id',), limit=1)
        if info:
            self.supplier.update('goods', condition={'goods_id': info['goods_id']}, data=goods_data)
            goods_id = info['goods_id']
            print('更新mysql成功，GoodsId：%s' % (goods_id,))
        else:
            goods_data['add_time'] = _unix_time - 8 * 3600
            goods_id = self.supplier.insert('goods', data=goods_data, return_insert_id=1)
            put_xs_list.append({
                'goods_id': goods_id,
                'goods_name': util.binary_type(goods_data['goods_name']),
                'goods_other_name': util.binary_type(goods_data['goods_other_name'])
            })
            print('保存mysql成功，GoodsId：%s' % (goods_id,))

        if not goods_id:
            return 0
        table_id = str(goods_id)[-1]
        if info:
            self.supplier.delete('goods_price_%s' % (table_id,), condition={'goods_id': goods_id})

        # 获取价格阶梯
        price_tiered = data['tiered']
        if not price_tiered:
            price_tiered.append((goods_data['min_buynum'], 0.0, 0.0))

        goods_price = []
        for p in price_tiered:
            qty = util.intval(p[0])
            if qty <= 0:
                continue
            goods_price.append({
                "purchases": p[0],
                "price": 0,
                "price_cn": p[2] * PRICE_PROPORTION,
            })

        self.supplier.insert('goods_price_%s' % (table_id,), data={
            'goods_id': goods_id,
            'price': json.dumps(goods_price),
        })

        tiered = []
        for p in goods_price:
            tiered.append([
                p["purchases"],
                p['price'],
                p['price_cn'],
            ])

        mongo_data = {
            'ModelName': goods_data['goods_name'],
            'OtherModelName': goods_data['goods_other_name'],
            'BrandName': goods_data['provider_name'],
            'DT': (goods_data['HDT'], goods_data['CDT']),
            'Desc': goods_data['goods_desc'],
            'GoodsId': goods_id,
            'GoodsSn': goods_data['goods_sn'],
            'Stock': (goods_data['goods_number'], goods_data['min_buynum'], 0),
            'Tiered': tiered,
            'error': 0,
            'time': int(time.time()),
            'url': goods_data['digikey_url'],
            'DocUrl': '',
            'increment': goods_data['increment']
        }

        # 保存mongodb
        collect = getattr(self.mongo, 'supplier')
        info = collect.find_one({'GoodsId': goods_id})
        if info:
            collect.update({'GoodsId': goods_id}, {"$set": mongo_data})
            print('更新mongodb成功，GoodsId：%s' % (goods_id,))
        else:
            collect.insert(mongo_data)
            print('保存mongodb成功，GoodsId：%s' % (goods_id,))
        # print('成功导入立创商城产品 %s 数据' % (data[4].encode('utf-8'),))
        return 1

    def put_queue_list(self, message_list, queue_name=None):
        '''提交信息至队列列表'''
        if not queue_name:
            return
        try:
            if not message_list:
                return
            if isinstance(message_list, dict):
                message_list = [message_list]
            connection = pika.BlockingConnection(pika.URLParameters(conf.AMQP_URL))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            for message in message_list:
                if 'goods_id' in message:
                    print 'GoodsId : %s 已提交队列至 %s' % (message['goods_id'], queue_name)
                message = json.dumps(message)
                channel.basic_publish(exchange='',
                                      routing_key=queue_name,
                                      body=message,
                                      properties=pika.BasicProperties(
                                          delivery_mode=2,  # 持久化
                                      ))
            connection.close()
        except Exception as e:
            _logger.exception('提交队列异常')
            return None

    def clear_data(self):
        """清除导入的数据"""
        _total_num = 0
        condition = {'PN2': PN2, 'goods_id': ('>', 0)}
        while 1:
            goods_list = self.supplier.select('goods', condition=condition, fields=('goods_id', 'goods_name'),
                                              order='goods_id ASC', limit=1000)
            if not goods_list:
                break
            for row in goods_list:
                table_id = str(row['goods_id'])[-1]
                self.supplier.delete('goods_price_%s' % (table_id,), condition={'goods_id': row['goods_id']})
                self.supplier.delete('goods', condition={'goods_id': row['goods_id']})
                print("成功删除淘芯城数据 %s => %s" % (row['goods_id'], row['goods_name'].encode('utf-8')))
                _total_num += 1
            condition['goods_id'] = ('>', row['goods_id'])
        return _total_num

    def check_goods(self):
        """检测数据有效性"""
        last_id = 0
        _total_num = 0
        collect = getattr(self.mongo, 'supplier')
        _unix_time = int(time.time()) - 8 * 3600
        while 1:
            condition = {
                'goods_id': ('>', last_id),
                'PN2': PN2
            }
            goods_list = self.supplier.select('goods', condition=condition,
                                              fields=('goods_id', 'last_update'),
                                              order='goods_id ASC',
                                              limit=1000)
            if not goods_list:
                break
            goods_id = 0
            for row in goods_list:
                goods_id = row['goods_id']
                if (row['last_update'] + 8 * 3600) >= self._start_time:
                    print('产品 %s 有效' % (goods_id,))
                else:
                    mongo_data = {
                        'error': 404,
                        'time': int(time.time()),
                    }
                    info = collect.find_one({'GoodsId': goods_id}, fields={'GoodsId': 1})
                    if info:
                        collect.update({'GoodsId': goods_id}, {"$set": mongo_data})
                        print('无效产品：%s, 更新mongodb成功' % (goods_id,))
                _total_num += 1
            last_id = goods_id
        # 更新供应商最后更新时间
        self.hqchip.update('suppliers', condition={'supplier_sn': PN2}, data={
            'last_update': _unix_time
        })
        return _total_num

    def get_ic_category(self, cat_list):
        """获取ic分类"""
        if not cat_list:
            return []
        k = '_'.join(cat_list)
        if 'category' not in self.__data:
            self.__data['category'] = {}
        if k in self.__data['category']:
            return self.__data['category'][k]
        i = 0
        cids = []
        for cat in cat_list:
            cat_ic = self.hqchip.select('category_ic', condition={
                                        'cat_name': cat}, fields=('cat_id',), limit=1)
            if cat_ic:
                cids.append(cat_ic[0])
                continue
            break
        return cids

    def get_ic_brand(self, brand_name):
        """获取创建品牌"""
        if not brand_name:
            return 0
        if isinstance(brand_name, unicode):
            brand_name = brand_name.encode('utf-8')
        if 'brand' not in self.__data:
            self.__data['brand'] = {}
        if brand_name in self.__data['brand']:
            return self.__data['brand'][brand_name]
        i = 0
        brand_ic = self.hqchip.select('brand_ic', condition={'brand_name': brand_name},
                                      fields=('brand_id',), limit=1)
        if brand_ic:
            return brand_ic['brand_id']
        ret = self.hqchip.select('brand_supplier', condition={'brand_name': brand_name},
                                 fields=('brand_id',), limit=1)
        if not ret:
            first_letter = brand_name[0]
            if not first_letter.isalpha():
                first_letter = '#'
            self.hqchip.insert('brand_supplier', data={
                'brand_name': brand_name,
                'first_letter': first_letter,
                'site_url': '',
            })
        return 0


def exception_notice(etype=''):
    """异常通知"""
    now_minuter = util.date(format='%Y-%m-%d %H:%M')
    subject = '【HQChip】合作库存 %s 数据更新异常通知 %s' % (PN2, now_minuter)
    if etype == 'mysql':
        except_msg = 'mysql数据库连接异常'
    elif etype == 'mongo':
        except_msg = 'mongodb 数据库连接异常'
    else:
        except_msg = '数据获取异常'
    body = "合作库存 %s 数据更新数据获取异常, 异常原因：%s,请注意检查！" % (PN2, except_msg)
    util.sendmail(conf.EMAIL_NOTICE.get(
        'accept_list'), subject=subject, body=body)


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)

    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-i', '--import', dest='action', help='导入合作库存数据数据，该操作将直接写入数据至数据库',
                        action='store_const', const='import')
    parser.add_argument('-c', '--clear', dest='action', help='清空导入的数据',
                        action='store_const', const='clear')
    parser.add_argument('-t', '--thead-num', dest='threadnum', help='抓取线程数数，默认为0，建议不要超过100',
                        default=0, type=int)
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        print "\n帮助示例"
        print "导入产品数据        %s -i" % sys.argv[0]
        print "指定抓取线程数      %s -i -t 5" % sys.argv[0]
        print "清除导入的数据      %s -c" % sys.argv[0]
        print
    elif args.action:
        HQChipSupplier(**args.__dict__)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main()

    def get_ic_category(cat_name):
        return 0

    def get_ic_brand(brand_name):
        return 0

    description_goods_data = {
        # cat_id 通过get_ic_category(cat_name)获得
        'cat_id': get_ic_category(data['cat_name']),  # 可以传入列表
        # 品牌ID制造商ID
        'brand_id': get_ic_brand(data['brand']),
        # 全局设置 PN2 = 'HQCHIP(site_name)'
        'PN2': PN2,
        # 产品名
        'goods_name': str(data['goods_name']),
        # 品牌
        'provider_name': str(data['brand']),
        # 产品标识 _sn = goods_sn + PN2
        # goods_sn = hashlib.md5(_sn).hexdigest()
        'goods_sn': data['goods_sn'],
        # 产品描述
        'goods_desc': data['goods_desc'],
        # 库存
        'goods_number_hk': data['hk_stock'] if 'hk_stock' in data else 0,
        'goods_number': data['cn_stock'] if 'cn_stock' in data else 0,
        # 增长量
        'increment': data['increment'],
        # 最小购买量
        'min_buynum': data['min_buynum'],
        # Date sheet
        'doc_url': '',
        # 图片url
        'goods_img': data['goods_img'],
        'goods_thumb': data['goods_img'],
        # 最后更新时间
        'last_update': int(time.time()),
        # 产品链接
        'digikey_url': data['url'],
        # 默认配置
        'DT_HK': HDT,
        'DT': CDT,
        'CDT': CDT,
        'HDT': HDT,
        'SPQ': 1,  # 最小包装 保持默认
        'batch_number': '',  # 批号 保持默认
        'encap': '',  # 包装规格 保持默认
        'brand_goods_id': 0,  # 保持默认
        'series': '',
        'source_type': 0,
        'user_id': 0,
        'log_id': 0,
        'to_china': 1,
        'to_hongkong': 0,
        'goods_weight': 0.0,
    }
