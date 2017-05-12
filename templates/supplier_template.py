#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    'Host': 'www.avnet.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.98 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://www.avnet.com/wps/portal/apac/',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'X-Requested-With': 'XMLHttpRequest',
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
    try:
        soup = BeautifulSoup(resp.text, 'lxml')
        if soup is None:
            logger.debug('初始化商品详情页面失败 URL: %s', resp.url)
            return -404
    except Exception as e:
        logger.debug('初始化商品详情页面失败 URL: %s ERROR: %s', (resp.url, util.traceback_info(e)))
        return -404
    # goods_sn
    url_path_list = resp.url.split('/')
    goods_sn_pattern = re.compile(r'.*-\d{19}')
    for path in url_path_list[::-1]:
        if goods_sn_pattern.findall(path):
            item['goods_sn'] = path
            break
    if not item.get('goods_sn', False):
        logger.debug("无法从链接中解析goods_sn URL: {url} ".format(url=resp.url))
        return -400
    # goods_name
    goods_info_div = soup.find('div', class_='section-left')
    item['goods_name'] = goods_info_div.find('h1').get_text(strip=True) if goods_info_div else item['goods_sn']
    # url
    item['url'] = resp.url
    # goods_img
    img_div = soup.find('div', id="outer-div1")
    img = img_div.find('img') if img_div else None
    item['goods_img'] = util.urljoin(resp.url, img.get('src')) if img else ''
    # goods_thumb
    item['goods_thumb'] = item['goods_img']
    # desc
    desc_p = soup.find('p', class_='RB-pdp_short_Desc')
    item['desc'] = desc_p.get_text(strip=True) if desc_p else ''
    # provider_name
    item['provider_name'] = "AVNET"
    # provider_url
    item['provider_url'] = ''
    # attr: [[None, None]]
    attr_body = soup.find('div', id="techAttr")
    attr_div = attr_body.find_all('div', class_='pdpDescriptionsBodyContent')
    attr = []
    if attr_div is not None:
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
    nav_ul = nav.find('ul', class_='nav')
    catlog = []
    if nav is not None:
        lis = nav.find_all('a')
        for a in lis:
            cat_name = a.get_text(strip=True)
            cat_url = util.urljoin(resp.url, a.get('href'))
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
