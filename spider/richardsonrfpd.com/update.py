#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by VinChan on 5/21/2017 0021

"""
goods_desc 使用desc代替
fetch_data 如果返回详情是list，那么fetch update需要增加对list的复制
如果解析的商品为系列商品，需要为每个商品添加product_id 和 family_sn 字段
"""

import os
import re
import sys
import copy
import math
import random
import logging
import requests
from bs4 import BeautifulSoup

try:
    import json
except ImportError:
    import simplejson as json

try:
    import packages.Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.Util as util

logger = logging.getLogger('hqchip_spider')
default_headers = {
            'Host': 'www.richardsonrfpd.com',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    """获取搜索数据"""
    if keyword:
        print '正在获取 avnet 中关键词：%s 的相关数据' % keyword
        url = "https://www.avnet.com/search/resources/store/715839038/productview/bySearchTerm/select?searchType=102&profileName=Avn_findProductsBySearchTermCatNav_Ajax&searchSource=Q&landingPage=true&storeId=715839038&catalogId=10001&langId=-1&currency=USD&orgEntityId=-2000&responseFormat=json&pageSize=20&pageNumber=1&_wcf.search.internal.boostquery=price_USD:{{0.00001+TO+*}}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075&_wcf.search.internal.filterquery=-newProductFlag%3ANPI&q={keyword}&intentSearchTerm={keyword}&searchTerm={keyword}&wt=json".format(keyword=keyword)
    elif 'url' in kwargs:
        url = kwargs['url']
    else:
        return 404
    _headers = copy.copy(default_headers)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    try:
        proxies = kwargs.get('proxies')
        if proxies is None and proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {
                'http': 'http://' + proxy[1][i],
                'https': 'https://' + proxy[1][i]
            }
        resp = requests.get(url, headers=_headers, timeout=30, proxies=proxies)
    except Exception as e:
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        if 'Invalid URL' not in str(e):
            data_dict['list'].append({
                'status': -400,
                'url': url,
                'id': id,
                'count': kwargs.get('count', 1)
            })
        return -400
    if resp.status_code != 200:
        if resp.status_code == 404 and '404.html' in resp.url:
            logger.info('STATUS:404; INFO:无效产品; URL: %s' % url)
            return 404
        logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (
            resp.status_code, proxies['http'] if proxy else '', url))
        data_dict['list'].append({
            'status': -405,
            'url': url,
            'id': id,
            'count': kwargs.get('count', 1)
        })
        return -405
    resp.encoding = 'utf-8'
    # 开始解析resp
    # 获取搜索的数量
    search_dict = {}
    try:
        search_dict = json.loads(resp.text.encode('utf-8'))
        product_list = search_dict.get('catalogEntryView', [])
    except:
        product_list = []
        logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
    if len(product_list) <= 0:
        data_dict['list'].append({
            'status': 404,
            'url': url,
            'id': id,
            'count': kwargs.get('count', 1)
        })
        return 404
    # sn = product.xpath('.//td[@class="partColHeader"]//span[@class="defaultSearchText"]')
    for product in product_list:
        goods_sn = product.get('seo_token_ntk', '')
        base_url = 'https://www.avnet.com/shop/apac/'
        product_url = product.get('avn_pdp_seo_path', '')
        data_dict['url'].append({
            'id': id,
            'url': util.urljoin(base_url, product_url),
            'goods_sn': goods_sn
        })
    if 'showMore=true' in url:
        return 200
    count = search_dict.get('recordSetTotal', 0)
    page_num = int(math.ceil(count / 20.0))
    if page_num <= 1:
        return 200
    max_list_num = util.intval(kwargs.get('max_list_num', 5))
    for x in xrange(2, page_num + 1):
        if max_list_num and x > max_list_num:
            break
        page_url = 'https://www.avnet.com/search/resources/store/715839038/productview/bySearchTerm/select?searchType=102&profileName=Avn_findProductsBySearchTermCatNav_More_Ajax&searchSource=Q&landingPage=true&storeId=715839038&catalogId=10001&langId=-1&currency=USD&orgEntityId=-2000&responseFormat=json&pageSize=20&pageNumber={next_page}&_wcf.search.internal.boostquery=price_USD:{{0.00001+TO+*}}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075&_wcf.search.internal.filterquery=-newProductFlag:NPI&q={keyword}&intentSearchTerm={keyword}&searchTerm={keyword}&showMore=true&wt=json'.format(next_page=x, keyword=keyword)
        # print page_url
        data_dict['list'].append({
            'id': id,
            'url': page_url,
        })
    return 200


def fetch_data(url, proxy=None, headers=None, **kwargs):
    """获取页面数据

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据
    """
    _headers = copy.copy(default_headers)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
        _headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'})
    if url[0:2] == '//':
        url = 'http:' + url
    try:
        proxies = kwargs.get('proxies')
        if proxies is None and proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {
                'http': 'http://' + proxy[1][i],
                'https': 'https://' + proxy[1][i]
            }
        resp = requests.get(url, headers=_headers, timeout=30, proxies=proxies)
    except Exception as e:
        # 将进行重试，可忽略
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    # 强制utf-8
    resp.encoding = 'utf-8'
    if '404.html' in resp.url:
        return 404
    return _parse_detail_data(resp, headers=_headers, **kwargs)


def _parse_detail_data(resp, headers=None, **kwargs):
    """
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    """
    item = {}
    root = lxml.html.fromstring(resp.text.encode('utf-8'))
    # goods_sn
    goods_sn_match = re.search(r'productId=(\d+)', resp.url)
    if goods_sn_match:
        item['goods_sn'] = goods_sn_match.group(1)
    else:
        logger.debug("解析 goods_sn 失败，重试URL:{url}".format(url=resp.url))
        return None
    # goods_name, provider_name
    try:
        title = root.xpath('//span[@class="ContentTitle"]')[0]
        item['goods_name'] = util.clear_text(title.text)
        provider_name = title.xpath('a')
        item['provider_name'] = util.clear_text(provider_name[0].text) if provider_name else ''
        item['provider_url'] = ''
    except IndexError:
        logger.debug("解析 goods_name 失败，重试URL:{url}".format(url=resp.url))
        return Request(url=resp.url, headers=self.headers)

    # goods_other_name
    goods_other_name = root.xpath('//span[@style="font-weight:bold;"]')
    for x in goods_other_name:
        match = re.search('MFG\s*Part\s*Number:\s*([^\s]+)', x.text, re.IGNORECASE)
        item['goods_other_name'] = match.group(1) if match else ''

    # catlog
    item['catlog'] = []
    catlog_div = root.xpath('//div[@class="breadcrumb"]//a')
    for catlog in catlog_div:
        catlog_name = util.clear_text(catlog.text)
        catlog_url = urlparse.urljoin(resp.url, catlog.xpath('./@href')[0])
        if catlog_name and catlog_url:
            item['catlog'].append([catlog_name, catlog_url])
        else:
            break

    # attr
    item['attr'] = []
    attr_table = root.xpath('//table[@class="PDTable"]//td')
    # TODO index error
    for x in range(0, len(attr_table), 2):
        attr_key = attr_table[x].text
        attr_value = attr_table[x + 1].text
        if attr_key and attr_value:
            attr_key = attr_key.strip(' ')
            attr_value = attr_value.strip(' ')
            item['attr'].append([attr_key, attr_value])
        else:
            break

    # rohs
    rohs_img = root.xpath('//img[@title="IsROHSCompliant"]')
    item['rohs'] = 1 if rohs_img else -1

    # doc
    doc_link = root.xpath('//a[@id="docDown"]/@href')
    item['doc'] = doc_link[0] if doc_link else ''

    #
    return item


def fetch_search_list(url, id=None, headers=None, proxy=None, **kwargs):
    """抓取搜索列表数据"""
    data_dict = {
        'detail': [],
        'list': [],
        'url': []
    }
    fetch_search_data(id=id, data_dict=data_dict, headers=headers, proxy=proxy, url=url, **kwargs)
    return data_dict


def fetch_update_data(url=None, id=None, **kwargs):
    """
    获取更新数据

    @description
        更新数据仅需要
        id          此处为GoodsId
        tiered      价格阶梯
        stock       库存
        desc        描述
        increment   递增量
    """
    headers = kwargs.get('headers')
    proxy = kwargs.get('proxy')
    goods_name = kwargs.get('goods_name')
    provider_name = kwargs.get('provider_name')
    data = fetch_data(url, headers=headers, proxy=proxy, fetch_update=True)
    res = {'id': id}
    if isinstance(data, dict):
        res['status'] = 200
        res['tiered'] = data['tiered']
        res['stock'] = data['stock']
        res['desc'] = data['desc']
        res['increment'] = data['increment']
        # 临时策略，用于更新旧数据，添加属性
        res['attr'] = data['attr']
        if goods_name is not None and goods_name != data['goods_name']:
            res['goods_name'] = data['goods_name']
        if provider_name is not None and provider_name != data['provider_name'] \
                and data['provider_name']:
            res['provider_name'] = data['provider_name']
        if 'goods_other_name' in data:
            res['goods_other_name'] = data['goods_other_name']
        if 'catlog' in data:
            res['catlog'] = data['catlog']
        if 'url' in data:
            res['url'] = data['url']
    else:
        res['status'] = data
        res['url'] = url
        res['count'] = kwargs.get('count', 1)
    return res


def fetcher(url, **kwargs):
    """获取URL数据"""
    if kwargs.get('headers', None):
        _headers = kwargs['headers']
    else:
        _headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
        }
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 20)
    data = kwargs.get('formdata')
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
        logger.info('请求异常 ; %s' % e)
        return None

    if rs.status_code != 200 and kwargs.get('error_halt', 1):
        logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None

    if 'return_response' in kwargs:
        return rs
    return rs.text


if __name__ == '__main__':
    data_dict = {
        'detail': [],
        'list': [],
        'url': []
    }
    import json

    fetch_search_data(keyword='lm358', data_dict=data_dict)
    print(json.dumps(data_dict))
    test_url = 'https://www.avnet.com/shop/apac/p/amplifiers/op-amp/on-semiconductor/lm358dr2g-3074457345629927117'
    # print json.dumps(fetch_data(test_url))
    print fetch_update_data(test_url)
