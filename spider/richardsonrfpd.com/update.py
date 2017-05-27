#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import lxml.html
import copy
import math
import random
import logging
import requests

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
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Host': 'www.richardsonrfpd.com',
    'Referer': 'http://www.richardsonrfpd.com/Pages/home.aspx',
}


def do_search(response=None, keyword=''):
    if response is None:
        return -404
    form_data = {}
    try:
        html = response.text.encode('utf-8')
        root = lxml.html.fromstring(html)
    except:
        return -404

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

    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$txtPartNumber'] = keyword
    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$ctl03'] = 'Starts with'
    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$btnSearch'] = 'Search'

    _headers = copy.copy(default_headers)
    _headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        resp = requests.post(url=response.url, headers=_headers, data=form_data, allow_redirects=False)
    except:
        return -400
    return resp


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    """获取搜索数据"""
    if keyword:
        print '正在获取 richardsonrfpd 中关键词：%s 的相关数据' % keyword
        url = 'http://www.richardsonrfpd.com/Pages/AdvanceSearch.aspx'
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
        response = requests.get(url, headers=_headers, timeout=30, proxies=proxies)
        resp = do_search(response, keyword)
        if isinstance(resp, int):
            raise ValueError
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
    if 'Search-Results.aspx' in resp.url:
        product_list = analyse_product_url(resp)
    root = lxml.html.fromstring(resp.text.encode('utf-8'))
    product_list = root.xpath('//tr[@valign="top"][@height=85]')
    if len(product_list) <= 0:
        data_dict['list'].append({
            'status': 404,
            'url': url,
            'id': id,
            'count': kwargs.get('count', 1)
        })
        return 404
    for product in product_list:
        detail = product.xpath('.//a[@class="lnk12b-blackOff"]')
        detail_url = util.urljoin(resp.url, detail[0].xpath('./@href')[0]) if detail else ''
        match = goods_sn_pattern.search(detail_url)
        if not match and detail_url:
            logger.debug(u"无法匹配链接中的goods_sn URL{url}".format(url=detail_url))
            return -404
        goods_sn = match.group(1)
        goods_name = detail[0].text_content() if detail else ''
        data_dict['url'].append({
            'id': id,
            'url': detail_url,
            'goods_sn': goods_sn,
            'goods_name': goods_name,
        })
    if 'showMore=true' in url:
        return 200
    count = root.xpath('//td[@class="medtext"]')
    count = util.number_format(count[0].text, places=0, index=999, smart=True) if count else 0
    page_num = int(math.ceil(count / 10.0))
    if page_num <= 1:
        return 200
    max_list_num = util.intval(kwargs.get('max_list_num', 5))
    page_list = root.xpath('//td[@class="medtext"]/a/@href')
    for x in xrange(1, page_num + 1):
        if max_list_num and x > max_list_num:
            break
        page_url = 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f?search={search}&range={start}%2C{end}%2C{total}'.format(
            search=keyword, start=x * 10 + 1, end=(x + 1) * 10, total=count)
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
    # goods_name
    goods_name = root.xpath('//td[@class="lnk11b-colorOff"]')
    item['goods_name'] = util.cleartext(goods_name[0].text) if goods_name else ''
    # goods_sn
    match = goods_sn_pattern.search(resp.url)
    item['goods_sn'] = match.group(1) if match else ''
    if not item['goods_name'] or not item['goods_sn']:
        logger.debug("无法解析goods_name和goods_sn URL:{url}".format(url=resp.url))
        return -404
    # goods_desc
    goods_desc = root.xpath('//td[@class="txt11"]/text()')
    item['desc'] = util.cleartext(goods_desc[0], '\n', '\t') if goods_desc else ''
    # tiered
    tiered = []
    price_list = root.xpath('//td[@class="texttable"]')
    for x in range(0, len(price_list), 2):
        qty = util.intval(price_list[x].text_content())
        price = util.floatval(price_list[x + 1].text_content())
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
    stock = root.xpath('//input[@id="custcol7"]/@value')
    stock = util.intval(stock[0]) if stock else 0
    item['stock'] = [stock, qty]
    # url
    item['url'] = resp.url
    # provider_name
    item['provider_name'] = 'LINEAR'
    item['provider_url'] = ''
    # doc catlog
    item['doc'] = ''
    item['catlog'] = ''
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
    # 一些信息需要在linear.com.cn获取
    return handle_of_redirects(item)


def handle_of_redirects(item=None):
    item = item if item else {}
    if not item:
        return -404
    search_url = 'http://www.linear.com.cn/search/index.php?q={search}'.format(search=item['goods_name'])
    _headers = copy.copy(default_headers)
    _headers.update({'Host': 'www.linear.com.cn'})
    resp = requests.get(url=search_url, headers=_headers, allow_redirects=False)
    location = util.urljoin(resp.url, resp.headers.get('Location'))
    if 'product/' in location or 'solutions/' in location:
        try:
            response = requests.get(url=location, headers=_headers)
        except:
            logger.error("获取目录和文档失败 URL{url}".format(url=location))
            return -404
        return parse_more(item, response)
    elif 'search.php' in location:
        try:
            response = requests.get(url=location, headers=_headers)
        except:
            logger.error("获取搜索列表 URL{url}".format(url=location))
            return -404
        return filter_search_result(item, response)


def parse_more(item=None, response=None):
    if not item or not response:
        return -404
    root = lxml.html.fromstring(response.text.encode('utf-8'))
    data = {}
    # family_sn
    match = family_sn_pattern.search(response.url)
    data['family_sn'] = match.group(1) if match else item['goods_name']
    # catlog
    breadcrumb = root.xpath('//p[@class="breadcrumb"]/a')
    data['catlog'] = []
    for catlog in breadcrumb:
        catlog_name = util.cleartext(catlog.text_content())
        catlog_url = util.urljoin(response.url, catlog.xpath('./@href')[0])
        if catlog_name and catlog_url:
            data['catlog'].append([catlog_name, catlog_url])
        else:
            data['catlog'] = []
            break
    else:
        data['catlog'].append([data['family_sn'], response.url])
    # doc
    doc = root.xpath('//li[@class="pdf"]/a[@class="doclink"]/@title')
    data['doc'] = "http://cds.linear.com/docs/en/datasheet/{title}".format(title=doc[0]) if doc else ''

    item.update(data)
    return item


def filter_search_result(item=None, response=None):
    if not item or not response:
        return -404
    root = lxml.html.fromstring(response.text.encode('utf-8'))
    search_result = root.xpath('//a[@class="search-keymatches-link"]/@href')
    if not search_result:
        item['catlog'] = []
        item['doc'] = ''
        item['family_sn'] = item['goods_name']
        return item
    match_num = 0
    real_link = ''
    for link in search_result:
        match_last_num = match_num
        family_sn = link.split('/')[-1]
        for x in family_sn:
            if x in item['goods_name']:
                match_num += 1
        if match_num > match_last_num:
            real_link = link
        match_num = 0
    _headers = copy.copy(default_headers)
    _headers.update({'Host': 'www.linear.com.cn'})
    try:
        resp = requests.get(url=real_link, headers=_headers)
        return parse_more(item, resp)
    except:
        return -404


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

    fetch_search_data(keyword='lt1001', data_dict=data_dict)
    print(json.dumps(data_dict))
    test_url = 'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.32523/.f'
    print json.dumps(fetch_data(test_url))

    print fetch_update_data(test_url)
