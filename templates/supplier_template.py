# -*- encoding: utf-8 -*-


''' 供应商 


'''



import os
import re
import sys
import copy
import math
import random
import logging
from w3lib.html import remove_tags
try:
    import json
except ImportError:
    import simplejson as json
import requests
import lxml.html
try:
    import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import Util as util


logger = logging.getLogger('hqchip_spider')
default_headers = {
    
}


def fetch_data(url, proxy=None, headers=None,**kwargs):
    '''获取页面数据

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据


    '''
    _headers = copy.copy(default_headers)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    if url[0:2] == '//':
        url = 'http:' + url
    # print url
    try:
        proxies = None
        if proxy:
            i = random.randint(0,proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        resp = requests.get(url, headers=_headers,timeout=30, proxies=proxies)
    except Exception as e:
        #将进行重试，可忽略
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    #强制utf-8
    resp.encoding = 'utf-8'
    if '404.html' in resp.url:
        return 404
    return _parse_detail_data(resp, headers=_headers, **kwargs)


def _parse_detail_data(resp, headers=None, **kwargs):
    '''
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    '''
    item = {}
    return item


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    '''获取搜索数据'''
    if keyword:
        print '正在获取 rs 中关键词：%s 的相关数据' % keyword
        url = 'http://china.rs-online.com/web/c/?sra=oss&r=t&searchTerm=%s' % keyword
    elif 'url' in kwargs:
        url = kwargs['url']
    else:
        return 404
    _headers = copy.copy(default_headers)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0]-1)
            proxies = {'http': 'http://' + proxy[1][i]}
        resp = requests.get(url, headers=_headers, timeout=30, proxies=proxies)
    except Exception as e:
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e),url))
        if 'Invalid URL' not in str(e):
            data_dict['list'].append({
                'status': -400,
                'url': url,
                'id': id,
                'count': kwargs.get('count',1)
            })
        return -400

    if resp.status_code != 200:
        if resp.status_code == 404 and '404.html' in resp.url:
            logger.info('STATUS:404; INFO:无效产品; URL: %s' % url)
            return 404
        logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (resp.status_code,proxies['http'] if proxy else '',url))
        data_dict['list'].append({
            'status':-405,
            'url': url,
            'id': id,
            'count': kwargs.get('count',1)
        })
        return -405
    resp.encoding = 'utf-8'
    root = lxml.html.fromstring(resp.text)
    try:
        # 检查是否搜索到商品
        product = root.xpath('//div[@id="base"]/table')[0]
    except:
        product = []
    if len(product) <= 0:
        logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        data_dict['list'].append({
            'status': -404,
            'url': url,
            'id': id,
            'count': kwargs.get('count',1)
        })
        return -404

    # 获取搜索列表中的商品链接
    links = product.xpath('.//a[@class="tnProdDesc"]')
    # sn = product.xpath('.//td[@class="partColHeader"]//span[@class="defaultSearchText"]')
    for vo in links:
        link = vo.xpath('./@href')[0]
        # goods_sn = util.cleartext(so.text, ' ').upper()
        goods_sn = re.search(r'/web/p/[^/?<>"]+/(\d+)/', link).group(1)
        data_dict['url'].append({
            'id': id, 
            'url': util.urljoin(resp.url, link),
            'goods_sn': goods_sn
        })

    # 获取分页链接
    match = re_katalog_url.search(resp.url)
    if not match:
        return 200
    category1 = match.group(1)
    category2 = match.group(2)
    product = match.group(3)
    page_num = 0
    count = 0
    try:
        count = util.number_format(root.xpath('//div[@class="viewProdDiv"]/text()')[0], places=0, index=999, smart=True)
        # print count
    except:
        count = 0
    page_num = int(math.ceil(count / 20.0))
    if page_num <= 1:
        return 200
    max_list_num = util.intval(kwargs.get('max_list_num', 5))
    for x in xrange(2, page_num + 1):
        if max_list_num and x > max_list_num:
            break
        page_url = 'http://china.rs-online.com/web/c/%s/%s/%s/?pn=%d' % (category1, category2, product, x)
        # print page_url
        data_dict['list'].append({
            'id': id, 
            'url': page_url,
        })
    return 200


def fetch_search_list(url, id=None, headers=None, proxy=None, **kwargs):
    '''抓取搜索列表数据'''
    data_dict = {
        'detail': [],
        'list': [],
        'url' : []
    }
    fetch_search_data(id=id, data_dict=data_dict, headers=headers, proxy=proxy, url=url,**kwargs)
    return data_dict


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    获取更新数据

    @description
        更新数据仅需要
        id          此处为GoodsId
        tiered      价格阶梯
        stock       库存
        desc        描述
        increment   递增量
    '''
    headers = kwargs.get('headers')
    proxy   = kwargs.get('proxy')
    goods_name = kwargs.get('goods_name')
    provider_name = kwargs.get('provider_name')
    data = fetch_data(url,headers = headers,proxy = proxy, fetch_update=True)
    res = {}
    res['id']       = id
    if isinstance(data, dict):
        res['status']   = 200
        res['tiered']   = data['tiered']
        res['stock']    = data['stock']
        res['desc']     = data['desc']
        res['increment']= data['increment']
        #临时策略，用于更新旧数据，添加属性
        res['attr']     = data['attr']
        if goods_name is not None and goods_name != data['goods_name']:
            res['goods_name']= data['goods_name']
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
        res['url']    = url
        res['count']  = kwargs.get('count', 1)
    return res


def fetcher(url, **kwargs):
    '''获取URL数据'''
    if kwargs.get('headers', None):
        _headers = kwargs['headers']
    else:
        _headers = {
            'user-agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
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
        logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code,url))
        return None

    if 'return_response' in kwargs:
        return rs
    return rs.text


if __name__ == '__main__':
    data_dict = {
        'detail': [],
        'list': [],
        'url' : []
    }
    import json
    fetch_search_data(keyword='lm358', data_dict=data_dict)
    print(json.dumps(data_dict))
    url = 'http://china.rs-online.com/web/p/position-sensors/1245987/'
    print fetch_update_data(url, 0)
    print fetch_data(url)
    search_url = 'http://china.rs-online.com/web/c/semiconductors/amplifiers-comparators/operational-amplifiers/?pn=3'
    print fetch_search_list(search_url,headers=default_headers)