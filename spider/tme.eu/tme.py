# -*- encoding: utf-8 -*-

import os
import re
import sys
import time
import copy
import math
import random
import logging

try:
    import json
except ImportError:
    import simplejson as json
import requests
import lxml.html
from config import APP_ROOT

try:
    import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import Util as util

logger = logging.getLogger('hqchip_spider')
default_headers = {
    'Host': 'www.tme.eu',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
}
# 国家中国，使用美元
default_cookies = {
    'limitTme': '50',
    'lang_tme': 'zh',
}

re_katalog_url = re.compile(r'/zh/katalog/[a-zA-Z\-]+\_(\d+)')


def login():
    login_url = 'https://www.tme.eu/zh/login/?back=http%3A%2F%2Fwww.tme.eu%2Fzh%2F'
    formdata = {
        'f_login': 'tme@mailinator.com',
        'f_password': 'Aa111111',
    }
    _headers = default_headers
    _headers.update({
        'Content-Length': '49',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.tme.eu/zh/login/?back=http%3A%2F%2Fwww.tme.eu%2Fzh%2F',
        'Origin': 'https://www.tme.eu',
    })
    print _headers
    response = requests.post(url=login_url, data=formdata, headers=_headers, allow_redirects=False)
    if response:
        return response.cookies
    else:
        return None


# def get_cookies():
#     cookies_save = 'tme_cookies'
#     on_sale_cookies = login()
#     if on_sale_cookies is not None:
#         cookies = {}
#         for vo in on_sale_cookies:
#             cookies[vo.name] = vo.value
#         util.file(cookies_save, cookies)


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''获取页面数据

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据


    '''
    _headers = copy.copy(default_headers)
    _cookies = copy.copy(default_cookies)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    if url[0:2] == '//':
        url = 'http:' + url
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        resp = requests.get(url, headers=_headers, cookies=_cookies,
                            timeout=30, proxies=proxies)
    except Exception as e:
        # 将进行重试，可忽略
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400

    # 强制utf-8
    resp.encoding = 'utf-8'
    if '/zh/ErrorPage/404.html' in resp.url:
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
    item['url'] = resp.url
    root = lxml.html.fromstring(resp.text)
    try:
        symbols = root.xpath("//div[contains(@class, 'symbols')]")[0]
        item['goods_sn'] = util.cleartext(
            symbols.xpath(".//td[contains(@class, 'product-symbol')]/@data-product-symbol")[0], ' ').upper()
        name = root.xpath('//div[@id="name-box"]/div/h1/text()')
        if len(name) > 1:
            item['goods_name'] = util.cleartext(name[1], ' ').upper()
        else:
            item['goods_name'] = util.cleartext(symbols.xpath('//tr[1]/td[@class="value"]/text()')[0], ' ').upper()
        provider = root.xpath('//div[@id="name-box"]/div/h1/span/text()')
        if provider:
            item['provider_name'] = util.cleartext(provider[0], '  ').upper()
        else:
            item['provider_name'] = ''
    except (IndexError, AttributeError):
        logger.exception('parse error, url: %s', resp.url)
        return -404
    item['goods_other_name'] = item['goods_sn']
    try:
        item['desc'] = util.cleartext(root.xpath('//div[@id="name-box"]/div/h2/text()')[0], '  ')
    except IndexError:
        item['desc'] = ''
    try:
        item['goods_img'] = root.xpath('//div[@id="foto-box"]/a/img/@src')[0]
        item['goods_img'] = util.urljoin(resp.url, item['goods_img'])
    except:
        item['goods_img'] = ''
    item['goods_thumb'] = item['goods_img']
    item['goods_original'] = item['goods_img']
    try:
        link = symbols.xpath('.//a[contains(@onclick, "producer-link")]')[0]
        item['provider_url'] = util.urljoin(resp.url, link.xpath('./@href')[0])
        if not item['provider_name']:
            item['provider_name'] = util.cleartext(root.xpath('./text()')[0], '  ').upper()
    except:
        item['provider_url'] = ''
    try:
        item['doc'] = root.xpath("//td[@class='filename']/a[contains(@class, 'Documentation')]/@href")[0]
        item['doc'] = util.urljoin(resp.url, item['doc'])
    except:
        item['doc'] = ''
    min_qty = 0
    increment = 1
    try:
        box = root.xpath("//div[@id='min-amount']/..")[0]
        slist = box.xpath('./div')
        min_qty = util.intval(slist[0].text_content())
        if len(slist) > 1:
            increment = util.intval(slist[1].text_content())
    except:
        pass
    item['tiered'] = [[0, 0.0]]
    item['stock'] = [0, min_qty]  # 库存
    item['increment'] = increment
    # 属性
    item['attr'] = []
    attrs = root.xpath("//div[@id='specification']/table/tr")
    for vo in attrs:
        try:
            tlist = vo.xpath('./td')
            name = util.cleartext(tlist[0].text_content(), ' ')
            value = util.cleartext(tlist[1].text_content(), ' ')
            if not name:
                continue
            item['attr'].append([name, value])
        except:
            pass
    # 分类
    item['catlog'] = []
    catelogs = root.xpath("//span[@class='category-path']/a")
    for vo in catelogs:
        try:
            url = util.urljoin(resp.url, vo.xpath('./@href')[0])
            if not re_katalog_url.search(url):
                continue
            text = util.cleartext(vo.xpath('./text()')[0], ' ')
            if not text:
                continue
            item['catlog'].append([text, url])
        except:
            pass
    proxies = kwargs.get('proxies')
    meta = {'item': item}
    headers['Referer'] = resp.url
    headers['X-Requested-With'] = 'XMLHttpRequest'
    formdata = {'symbol': item['goods_sn'], 'brutto': ''}
    url = 'http://www.tme.eu/zh/_ajax/ProductInformationPage/_getStocks.html'
    try:
        cookies_save = 'tme_cookies'
        file_path = os.path.join(APP_ROOT, 'database', cookies_save)
        first_write = not os.path.exists(file_path)
        if int(time.time() % 3600) == 3599 or first_write:
            on_sale_cookies = login()
            if on_sale_cookies is not None:
                cookies = {}
                for vo in on_sale_cookies:
                    cookies[vo.name] = vo.value
                util.file(cookies_save, cookies)
        else:
            on_sale_cookies = util.file(cookies_save)
        print on_sale_cookies
        item = _parse_stock_price(url, meta=meta, headers=headers, formdata=formdata, proxies=proxies,
                                  cookies=on_sale_cookies)
    except Exception as e:
        logger.exception('获取解析价格库存异常')
        return -404
    print('型号: %s 数据获取成功!' % item['goods_name'])
    return item


def _parse_stock_price(url, **kwargs):
    """解析获取价格库存信息"""
    item = kwargs['meta'].get('item')
    resp = fetcher(url, return_response=1, hide_print=1, **kwargs)
    if not item:
        logger.error('request meta data error, url: %s', resp.url)
        return None
    try:
        data = json.loads(resp.text.encode('utf-8'))
        for vo in data['Products']:
            symbol = vo['symbol'].encode('utf-8')
            if symbol != item['goods_sn']:
                continue
            item['stock'][0] = util.intval(vo['InStock'])
            if item['stock'][0] < 0:
                item['stock'][0] = 0
            root = lxml.html.fromstring(vo['PriceTpl'].encode('utf-8'))
            prices = root.xpath("//tr")
            item['tiered'] = []
            for vo in prices:
                try:
                    tlist = vo.xpath('./td')
                    # print [x.text_content() for x in tlist]
                    qty = util.intval(tlist[0].text_content())
                    price = util.floatval(tlist[2].text_content())
                    if not qty or (item['tiered'] and qty < item['tiered'][-1][0]):
                        continue
                    item['tiered'].append([qty, price])
                except:
                    pass
                if not item['tiered']:
                    item['tiered'].append([0, 0.0])
            break
    except Exception:
        logger.error('parse stock price error, goods_sn: %s', item['goods_sn'])
        raise
    return item


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    """获取搜索数据"""
    if keyword:
        print '正在获取 tme 中关键词：%s 的相关数据' % keyword
        url = 'http://www.tme.eu/zh/katalog/?search=%s&cleanParameters=1' % keyword
    elif 'url' in kwargs:
        url = kwargs['url']
    else:
        return 404
    _headers = copy.copy(default_headers)
    _cookies = copy.copy(default_cookies)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        resp = requests.get(url, headers=_headers, cookies=_cookies,
                            timeout=30, proxies=proxies)
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
        if resp.status_code == 404 and '/zh/ErrorPage/404.html' in resp.url:
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
    root = lxml.html.fromstring(resp.text)
    try:
        product = root.xpath("//table[@id='products']")[0]
    except:
        product = []
    if len(product) <= 0:
        logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
        data_dict['list'].append({
            'status': -404,
            'url': url,
            'id': id,
            'count': kwargs.get('count', 1)
        })
        return -404
    links = product.xpath(".//a[contains(@class, 'product-symbol')]")
    for vo in links:
        link = vo.xpath('./@href')[0]
        goods_sn = util.cleartext(vo.text, ' ').upper()
        data_dict['url'].append({
            'id': id,
            'url': util.urljoin(resp.url, link),
            'goods_sn': goods_sn
        })
    if 'page=' in resp.url:
        return 200
    match = re_katalog_url.search(resp.url)
    if not match:
        return 200
    id_category = match.group(1)
    try:
        count = util.intval(resp.xpath('//div[@id="catalogue-header"]')[0].text)
    except:
        count = 0
    page_num = int(math.ceil(count / 50.0))
    if page_num <= 1:
        return 200
    max_list_num = util.intval(kwargs.get('max_list_num', 5))
    for x in xrange(2, page_num + 1):
        if max_list_num and x > max_list_num:
            break
        page_url = 'http://www.tme.eu/zh/katalog/?id_category=%s&page=%s&limit=50' % (id_category, x)
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
        'url': []
    }
    fetch_search_data(id=id, data_dict=data_dict, headers=headers, proxy=proxy, url=url, **kwargs)
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
    proxy = kwargs.get('proxy')
    goods_name = kwargs.get('goods_name')
    provider_name = kwargs.get('provider_name')
    data = fetch_data(url, headers=headers, proxy=proxy, fetch_update=True)
    res = {}
    res['id'] = id
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
    '''获取URL数据'''
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
    # fetch_search_data(keyword='lm358', data_dict=data_dict)
    # print(data_dict)
    # url = 'http://www.tme.eu/zh/details/40.31.8.024.000/minidiancijidianqi/finder/403180240000/'
    t_url = 'http://www.tme.eu/zh/details/3339p-1-101lf/516yingcunduoquankediaothtdianzuqi/bourns/'
    print fetch_update_data(t_url)
    # print login()
