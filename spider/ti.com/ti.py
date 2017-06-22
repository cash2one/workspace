# -*- encoding: utf-8 -*-


""" 供应商 ti.com """

import os
import re
import sys
import copy
import math
import random
import logging
import urlparse
from bs4 import BeautifulSoup

try:
    import json
except ImportError:
    import simplejson as json
import requests

try:
    import packages.Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import packages.Util as util

logger = logging.getLogger('hqchip_spider')
default_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
}


def fetch_data(url, proxy=None, headers=None, **kwargs):
    """获取页面数据

    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数，如fetch_update其表示是否为获取更新


    @return
        获取数据异常时返回信息为负值，成功为字典类型数据
        :param url:


    """
    if 'goods_sn' in kwargs:
        del kwargs['goods_sn']
    _headers = copy.copy(default_headers)
    if isinstance(headers, dict):
        _headers.update(util.rfc_headers(headers))
    if url[0:2] == '//':
        url = 'http:' + url
    try:
        proxies = None
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        ti_domain = urlparse.urlsplit(url)[1]
        if 'www.ti.com.cn' == ti_domain:
            product_path_pattern = re.compile(r'/cn/(.*)', re.IGNORECASE)
            product_path = product_path_pattern.search(url)
            if product_path:
                url = "http://www.ti.com/product/{path}".format(path=product_path.group(1))
        elif 'store.ti.com' in ti_domain:
            kwargs['proxies'] = proxies
            return _parse_store_ti_com(url, **kwargs)
        resp = requests.get(url, headers=_headers, timeout=30, proxies=proxies)
    except Exception as e:
        # 将进行重试，可忽略
        logger.debug('STATUS:-400 ; INFO:数据请求异常, %s ; URL:%s' % (util.traceback_info(e), url))
        return -400
    # 是否需要添加500的判断
    # 强制utf-8
    resp.encoding = 'utf-8'
    if '404.html' in resp.url:
        return 404
    if '/tool/' in resp.url:
        return _parse_tool_detail(resp, **kwargs)
    kwargs['proxies'] = proxies
    return _parse_detail_data(resp, headers=_headers, **kwargs)


def _parse_store_ti_com(url, **kwargs):
    goods_sn = re.search(r'com/(.*)\.aspx', url)
    if goods_sn:
        goods_sn = goods_sn.group(1)
    search_dict = {'detail': [], 'list': [], 'url': []}
    search_url = 'http://www.ti.com/sitesearch/docs/partnumsearch.tsp?sort=asc&linkId=2&filter=p&sortBy=pstatus&searchTerm={keyword}'.format(keyword=goods_sn)
    try:
        rs = requests.get(url=search_url,
                          headers=kwargs.get('headers', default_headers),
                          proxies=kwargs.get('proxies', None),
                          timeout=8)
        if rs.status_code == 200:
            search_dict = {'detail': [], 'list': [], 'url': []}
            fetch_search_data(keyword=goods_sn, data_dict=search_dict, other_usage=True)
    except requests.ReadTimeout, requests.ConnectTimeout:
        rs = -400
    if rs == 200:
        detail_url = ''
        if len(search_dict['url']) == 1:
            detail_url = search_dict['url'][0]['url']
        elif len(search_dict['url']) > 1:
            for x in search_dict['url']:
                if x['goods_sn'] in goods_sn or goods_sn in x['goods_sn']:
                    detail_url = x['url']
                    break
        if detail_url:
            item = fetch_data(detail_url, **kwargs)
            return item
        else:
            return -400
    else:
        try:
            proxies = kwargs.get('proxies')
            html = requests.get(url, headers=default_headers, proxies=proxies)
            soup = BeautifulSoup(html.content, 'lxml')
        except Exception as e:
            logger.exception(u'解析失败, 商品详情 URL: %s ' % url)
            return -400
        if html.status_code == 200:
            item = {}
            _desc = soup.find('tr', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_BuyProductDialog1_trSku')
            item['goods_name'] = _desc.find('h1').get_text(strip=True) if _desc else ''
            item['goods_sn'] = item['goods_name']
            item['desc'] = _desc.get_text(strip=True) if _desc else ''
            _img = soup.find('img', id='ProductImage')
            item['goods_img'] = util.urljoin(url, _img.get('src'))
            stock_info = get_stock(goods_sn=goods_sn, url=url)
            if stock_info:
                item['stock'] = [util.intval(stock_info[0]), 1]
                item['tiered'] = stock_info[1]
            else:
                item['stock'] = [0, 1]
                item['tiered'] = [[0, 0.00]]
            item['provider_name'] = 'TI'
            item["increment"] = 1
            item['url'] = url
            return item


# def _parse_store_ti_com(url, **kwargs):
#     """
#     更新数据仅需要
#         id          此处为GoodsId
#         tiered      价格阶梯
#         stock       库存
#         desc        描述
#         increment   递增量
#     """
#     goods_sn = re.search(r'com/(.*)\.aspx', url)
#     if goods_sn:
#         goods_sn = goods_sn.group(1)
#     else:
#         try:
#             proxies = kwargs.get('proxies')
#             html = requests.get(url, headers=default_headers, proxies=proxies)
#             soup = BeautifulSoup(html.content, 'lxml')
#         except:
#             logger.exception(u'解析失败, 商品详情 URL: %s ' % url)
#             return -400
#         if not html.status_code == 200:
#             goods_desc = soup.find('tr', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_BuyProductDialog1_trSku')
#             goods_sn = goods_desc.find('h1').get_text(strip=True) if goods_desc else ''
#         else:
#             goods_sn = ''
#     if not goods_sn:
#         logger.exception(u'获取商品goods_sn失败, 商品详情 URL: %s ' % url)
#         return -400
#     else:
#         search_dict = {'detail': [], 'list': [], 'url': []}
#         fetch_search_data(keyword=goods_sn, data_dict=search_dict, other_usage=True)
#         detail_url = ''
#         if len(search_dict['url']) == 1:
#             detail_url = search_dict['url'][0]['url']
#         elif len(search_dict['url']) > 1:
#             for x in search_dict['url']:
#                 if x['goods_sn'] in goods_sn or goods_sn in x['goods_sn']:
#                     detail_url = x['url']
#                     break
#         if detail_url:
#             item = fetch_data(detail_url, **kwargs)
#             return item
#         else:
#             return -400


def _parse_tool_detail(resp, **kwargs):
    items = {'list': []}
    item = {}
    pattern_gpn = re.compile(r'/tool/([^/\?\.%]+)')
    # gpn
    gpn = pattern_gpn.search(resp.url).group(1)
    try:
        soup = BeautifulSoup(resp.text.encode('utf-8'), 'lxml')
    except:
        logger.exception('Parse Error Product URL: %s' % resp.url)
        return -403
    # category
    breadcrumb_div = soup.find('div', class_='breadcrumbs')
    cat_log = []
    if breadcrumb_div:
        for a in breadcrumb_div.find_all('a'):
            if 'TI Home' in a.get_text(strip=True):
                continue
            cat_log.append([a.get_text(strip=True), a['href']])
    item['catlog'] = cat_log if cat_log else []
    # 添加默认值
    item['provider_name'] = ''
    item['provider_url'] = ''
    item['increment'] = 1
    item['rohs'] = -1
    # attr
    item['attr'] = []
    # doc
    item['doc'] = ''
    # url
    item['url'] = resp.url
    # goods_img, goods_thumb
    item['goods_img'] = ''
    item['goods_thumb'] = ''
    # pretty table
    table = soup.find('table', attrs={'class': 'tblstandard'})
    if not table:
        logger.exception('No Product in URL: %s' % resp.url)
        return
    trs = table.find_all('tr')[1:]
    for tr in trs:
        # goods_sn:description
        if 'Contact a Distributor' in tr.get_text(strip=True):
            break
        try:
            part = tr.find('h2').get_text(strip=True).split(':')
        except:
            desc = soup.find('h1', id="mainHeader")
            desc = desc.get_text(strip=True) if desc else ''
            part = [gpn, desc]
        item['goods_sn'] = part[0]
        item['goods_name'] = part[0]
        item['goods_other_name'] = ''
        item['desc'] = part[1]
        # price
        price = re.search(r'\$(\d+.?\d+)\(USD\)', tr.get_text(strip=True))
        price = price.group(1) if price else 0.00
        item['provider_name'] = 'TI' if price else ''
        item['tiered'] = [[1, util.floatval(price)]] if not util.floatval(price) == 0.0 else [[0, 0.00]]
        # 需要询价
        item['stock'] = [0, 1]
        items['list'].append(copy.copy(item))
    if not items['list']:
        logger.debug('status: -403; 解析商品详情失败, url: %s', str(resp.url))
        return -403
    return items


# def get_data_sheet(gpn, **kwargs):
#     url = 'http://www.ti.com/lit/gpn/%s' % gpn
#     doc_url = ''
#     try:
#         proxies = kwargs.get('proxies')
#         html = requests.get(url=url, headers=default_headers, allow_redirects=False,
#                             proxies=proxies)
#     except:
#         return doc_url
#     pattern_redirect_url = re.compile(r'<a href="(.*)">')
#     redirect_url = pattern_redirect_url.search(html.content)
#     redirect_url = redirect_url.group(1) if redirect_url else ''
#     if redirect_url:
#         redirect_url = redirect_url.replace(r'&amp;', '&')
#         try:
#             pdf_page = requests.get(url=redirect_url, headers=default_headers, allow_redirects=False,
#                                     timeout=30, proxies=proxies)
#         except:
#             return doc_url
#         pattern_doc_url = re.compile(r"window.location\s*=\s*'(http://.*\.pdf)'")
#         doc_url = pattern_doc_url.search(pdf_page.content)
#         doc_url = doc_url.group(1) if doc_url else ''
#     else:
#         return doc_url
#     return doc_url


# def get_tiered(url, **kwargs):
#     tiered = []
#     try:
#         proxies = kwargs.get('proxies')
#         html = requests.get(url=url, headers=default_headers, timeout=30, proxies=proxies)
#     except:
#         return [[0, 0.00]]
#     # 如果重定向则不存在该商品
#     if html.status_code == 200:
#         soup = BeautifulSoup(html.content, 'lxml')
#         table = soup.find('table', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_BuyProductDialog1_PricingTierList')
#         if table:
#             for tr in table.find_all('tr')[1:]:
#                 tds = tr.find_all('td')
#                 qty = tds[0].get_text(strip=True)
#                 price = tds[1].get_text(strip=True)
#                 tiered.append([util.intval(qty), util.floatval(price)])
#         else:
#             tiered = [[0, 0.00]]
#     else:
#         tiered = [[0, 0.00]]
#     return tiered


def get_stock(goods_sn, url, **kwargs):
    """ 从购物车中获取真实的商品库存 """
    session = requests.Session()
    session.headers = default_headers
    stock = 0
    ok = add_to_cart(url, session, **kwargs)
    retry = 2
    while retry > 0 and not ok:
        logger.info("请求添加购物车失败，正在重试")
        ok = add_to_cart(url, session, **kwargs)
        retry -= 1
    tiered = [[0, 0.00]]
    if isinstance(ok, list):
        tiered = ok
    if not ok:
        logger.error("获取库存失败")
        return stock, tiered
    goods = look_at_basket(session, **kwargs)
    retry = 2
    while retry > 0 and not goods:
        logger.error("查询购物车失败，正在重试")
        goods = look_at_basket(session, **kwargs)
        retry -= 1
    if not goods:
        logger.error("获取库存失败")
        return stock, tiered
    if goods_sn in goods:
        stock = goods[goods_sn]
    session.close()
    return stock, tiered


def add_to_cart(url, only_session, **kwargs):
    form_data = {
        "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$BuyProductPanel|ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$btnBuyPaid",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "",
        "__VIEWSTATEGENERATOR": "",
        "__VIEWSTATEENCRYPTED": "",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$SearchPhrase": "",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$hiLastHeaderAction": "none",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$hiSearchFilterValue": "none",
        "__ASYNCPOST": "true",
        "ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$btnBuyPaid": "Buy",
    }
    proxies = kwargs.get('proxies')
    try:
        stock_page = only_session.get(url=url, proxies=proxies)
    except:
        return 0
    if stock_page.status_code == 200:
        soup = BeautifulSoup(stock_page.content, 'lxml')
        view_state = soup.find('input', id="__VIEWSTATE")
        form_data['__VIEWSTATE'] = view_state.value if view_state else ''
        view_state_generator = soup.find('input', id="__VIEWSTATEGENERATOR")
        form_data['__VIEWSTATEGENERATOR'] = view_state_generator.value if view_state_generator else ''
        # tiered
        tiered = []
        table = soup.find('table', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_BuyProductDialog1_PricingTierList')
        if table:
            for tr in table.find_all('tr')[1:]:
                tds = tr.find_all('td')
                qty = tds[0].get_text(strip=True)
                price = tds[1].get_text(strip=True)
                tiered.append([util.intval(qty), util.floatval(price)])
        else:
            tiered = [[0, 0.00]]
    else:
        return 0
    # post
    try:
        resp = only_session.post(url=url, data=form_data, proxies=proxies)
    except:
        return 0
    # print resp.content
    return tiered


def look_at_basket(only_session, **kwargs):
    basket_url = 'https://store.ti.com/Basket.aspx'
    proxies = kwargs.get('proxies')
    try:
        basket_page = only_session.get(basket_url, proxies=proxies)
    except:
        return 0
    soup = BeautifulSoup(basket_page.content, 'lxml')
    table = soup.find('table', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_ProductList')
    rows = table.find_all('td', class_='cartRow') if table else []
    goods_data = {}
    for goods in rows:
        goods_sn = goods.find('span', class_='productSku').get_text(strip=True)
        # print goods_sn
        goods_stock = goods.find('div', class_='prodStock').get_text(strip=True)
        # print goods_stock
        goods_data[goods_sn] = goods_stock
    return goods_data


def get_detail(gpn=None, **kwargs):
    data = dict()
    if not gpn:
        yield data
        # return product_list
    url = "http://www.ti.com/product/%s/samplebuy" % gpn
    try:
        proxies = kwargs.get('proxies')
        html = requests.get(url=url, headers=default_headers, timeout=30, proxies=proxies)
        if 'Page not found' in html.content:
            raise StopIteration
    except:
        raise StopIteration
    if html.status_code != 200:
        raise StopIteration
    soup = BeautifulSoup(html.content, "lxml")
    # category
    breadcrumb_div = soup.find('div', class_='breadcrumb')
    breadcrumb_div = breadcrumb_div.find_all('a') if breadcrumb_div else []
    cat_log = []
    for a in breadcrumb_div:
        if 'TI Home' in a.get_text(strip=True):
            continue
        cat_log.append([a.get_text(strip=True), a['href']])
    data['catlog'] = cat_log if cat_log else []
    # goods_img, goods_thumb
    img_div = soup.find('div', class_='image')
    img = img_div.img['src'] if img_div else ''
    data['goods_img'] = img
    data['goods_thumb'] = img
    # pretty table
    table = soup.find('table', id='tblBuy')
    # 存在一些GPN商品组内没有商品列表，直接返回默认值
    if not table:
        data['goods_sn'] = gpn
        data['tiered'] = [[0, 0.00]]
        data['stock'] = [0, 1]
        yield data
    body_div = table.tbody if table else None
    # 如果获取不到商品列表就退出
    if not body_div:
        raise StopIteration
    ths = table.find_all('th') if table else []
    th_td = dict()
    for th in ths:
        if 'Part' in th.get_text(strip=True):
            th_td['PartNum'] = ths.index(th)
        if 'Price' in th.get_text(strip=True):
            th_td['Price'] = ths.index(th)
        if 'Inventory' in th.get_text(strip=True):
            th_td['Inventory'] = ths.index(th)
    tds = body_div.find_all('td') if body_div else []
    step = len(ths)
    tr = [tds[x:x + step] for x in range(0, len(tds), step)]
    total_parts = len(tr)
    for td in tr:
        logger.info("GPN:%s 共有%d个商品需要抓取，正在抓取第%d个。" % (gpn.encode('utf-8'), total_parts, tr.index(td) + 1))
        # tiered
        price = th_td.get('Price')
        pattern_price = re.compile(r'\s*(\d+.\d+)\s*\|\s*(\d+)ku\s*')
        if td[price].script:
            td[price].script.extract()
        tiered = pattern_price.search(td[price].get_text())
        if tiered:
            price = tiered.group(1)
            qty = int(tiered.group(2)) * 1000
            data['tiered'] = [[util.intval(qty), util.floatval(price)]]
        else:
            data['tiered'] = [[0, 0.00]]
        # goods_sn
        part_num = th_td.get('PartNum')
        data['goods_sn'] = ''
        for x in td[part_num].contents:
            if x.name == 'script':
                continue
            elif x.name == 'a':
                data['goods_sn'] = str(x.string).strip()
                # data['tiered'] = get_tiered(x['href'], **kwargs)
                stock, tiered = get_stock(data['goods_sn'], x['href'], **kwargs)
                data['tiered'] = tiered
                data['url'] = x['href']
                data['provider_name'] = 'TI'
                data['stock'] = [util.intval(stock), 1]
            elif x.string and str(x.string).strip():
                data['goods_sn'] = str(x.string).strip()
                data['stock'] = [0, 1]
                data['provider_name'] = ''
                # data['url'] = "https://store.ti.com/%s.aspx" % data['goods_sn']
                data['url'] = "http://www.ti.com/product/%s" % gpn
        yield data


def _parse_detail_data(resp, headers=None, **kwargs):
    """
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    """
    items = {'list': []}
    item = {}
    """解析系列型号数据"""
    # gpn
    pattern_gpn = re.compile(r'/product/([^/\?\.%&]+)')
    gpn = pattern_gpn.search(resp.url)
    if not gpn:
        logger.debug('status: -403; 解析商品详情失败, url: %s', str(resp.url))
        return -403
    gpn = gpn.group(1)
    soup = BeautifulSoup(resp.text.encode('utf-8'), 'lxml')
    # family_sn
    item['family_sn'] = gpn.upper()
    item['product_id'] = item['family_sn']
    # category
    breadcrumb_div = soup.find('div', class_='breadcrumb')
    cat_log = []
    if breadcrumb_div:
        for a in breadcrumb_div.find_all('a'):
            if 'TI Home' in a.get_text(strip=True):
                continue
            cat_log.append([a.get_text(strip=True), a['href']])
    item['catlog'] = cat_log if cat_log else []
    # goods_img, goods_thumb
    img_div = soup.find('div', class_='image')
    img = img_div.img['src'] if img_div else ''
    item['goods_img'] = img
    item['goods_thumb'] = img
    # attr
    attr = []
    params_table = soup.find('table', id='paramsName')
    data_table = soup.find('table', id='parametricdata')
    if params_table and data_table:
        attr_params = params_table.find_all('td')[0:-1]
        attr_data = data_table.find_all('td', class_='on')[0:-1]
        for k, v in zip(attr_params, attr_data):
            pattern_blank = re.compile('\s+')
            k = pattern_blank.sub(' ', k.get_text(strip=True))
            v = pattern_blank.sub(' ', v.get_text(strip=True))
            attr.append([k, v])
    item['attr'] = attr
    # doc
    doc_url = soup.find('a', class_='local')
    item['doc'] = util.cleartext(doc_url.get('href')) if doc_url else ''
    # description
    desc = soup.find('h1', class_='productTitle')
    item['desc'] = desc.get_text(strip=True) if desc else ''
    for p in get_detail(gpn, **kwargs):
        item['goods_sn'] = p.get('goods_sn', '')
        if not item['goods_sn']:
            continue
        item['goods_name'] = p.get('goods_sn', '')
        item['goods_other_name'] = ''
        item['url'] = p.get('url', '')
        # item['doc'] = get_data_sheet(gpn, **kwargs)
        item['stock'] = p.get('stock', [0, 1])
        item['tiered'] = p.get('tiered', [[0, 0.0]])
        # 添加供应商品牌
        item['provider_name'] = p.get('provider_name', '')
        item['provider_url'] = ''
        item['increment'] = 1
        item['rohs'] = -1
        items['list'].append(copy.copy(item))
    if not items['list']:
        logger.debug('status: -403; 解析商品详情失败, url: %s', str(resp.url))
        return -403
    return items


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    """获取搜索数据"""
    if keyword:
        if not kwargs.get('other_usage', False):
            print '正在获取 ti.com 中关键词：%s 的相关数据' % keyword
        url = 'http://www.ti.com/sitesearch/docs/partnumsearch.tsp?sort=asc&linkId=2&filter=p&sortBy=pstatus&searchTerm=%s' % keyword
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
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
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
    resp_json = {}
    try:
        resp_json = json.loads(resp.content)
        product = resp_json.get('response', {}).get('searchResults', {}).get('PartNoArray', [])
        # print len(product)
    except:
        product = []
        logger.debug('STATUS:-404 ; INFO:数据异常 ; URL:%s' % url)
    if len(product) <= 0:
        data_dict['list'].append({
            'status': 404,
            'url': url,
            'id': id,
            'count': kwargs.get('count', 1)
        })
        return 404
    links = product
    for vo in links:
        pn = vo.get('PartNumber', '')
        tn = vo.get('PartType', '')
        if pn:
            link = 'http://www.ti.com/product/%s' % pn
            if 'tool' in tn:
                link = 'http://www.ti.com/tool/%s' % pn
            data_dict['url'].append({
                'id': id,
                'url': link,
                'goods_sn': pn
            })
    if 'startNum=' in resp.url:
        return 200
    page_num = 0
    count = 0
    try:
        count = resp_json.get('response', {}).get('searchResults', {}).get('filter', {}).get('MaxRecordCount', '')
        count = util.intval(count)
    except:
        count = 0
    page_num = int(math.ceil(count / 25.0))
    if page_num <= 1:
        return 200
    # 翻页的form_data
    max_list_num = util.intval(kwargs.get('max_list_num', 5))
    for x in xrange(1, page_num + 1):
        if max_list_num and x > max_list_num:
            break
        url = 'http://www.ti.com/sitesearch/docs/partnumsearch.tsp?sort=asc&linkId=2&startNum=%d&filter=p&sortBy=pstatus&searchTerm=%s' % (
            25 * x, keyword)
        page_url = url
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
    res = {'id': id}
    if isinstance(data, dict) and data.get('list', False):
        res['status'] = 200
        res['list'] = data['list']
    elif isinstance(data, dict):
        res['status'] = 200
        res['tiered'] = data['tiered']
        res['stock'] = data['stock']
        res['desc'] = data['desc']
        res['increment'] = data['increment']
        # 临时策略，用于更新旧数据，添加属性
        if 'attr' in data:
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
        _headers = copy.copy(default_headers)
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 20)
    data = kwargs.get('formdata')
    if 'goods_sn' in kwargs:
        del kwargs['goods_sn']
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

    # fetch_search_data(keyword='ADC121S101CIMF ', data_dict=data_dict)
    # print(json.dumps(data_dict))
    # test_url = "http://www.ti.com/product/LMV771/samplebuy"
    # test_url = "http://www.ti.com/product/UCC37322"
    # store_url = 'http://www.ti.com/product/ADC121S101'
    store_url = "https://store.ti.com/LM358AMX/NOPB.aspx"

    # print fetch_data(store_url)
    print fetch_update_data(store_url)
    # ti_com_cn = 'http://www.ti.com.cn/product/cn/tps3803g15'
    # print json.dumps(fetch_data(store_url))
    # print fetch_search_list(search_url,headers=default_headers)
    # rs = requests.get(url=store_url, headers=default_headers)
    # print _parse_store_ti_com(rs)
