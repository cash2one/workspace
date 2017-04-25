# coding=utf-8
import re
import math
import json
import logging
import hashlib
import urlparse
import requests
from tools import box
from bs4 import BeautifulSoup

_logger = logging.getLogger('hqchip_spider')

headers_str = """
Host: www.supchip.com
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Referer: http://www.supchip.com/
Accept-Encoding: gzip, deflate, sdch
Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
"""
default_headers = box.headers_to_dict(headers_str)


def fetcher(url, data=None, **kwargs):
    """获取URL数据"""
    if kwargs.get('headers', None):
        _headers = kwargs['headers']
    else:
        _headers = {'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4', 'Accept-Encoding': 'gzip, deflate, sdch', 'Connection': 'keep-alive', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36', 'Host': 'www.supchip.com', 'Referer': 'http://www.supchip.com/'}
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 30)
    params = kwargs.get('params')
    try:
        if 'method' in kwargs:
            method = kwargs['method']
        else:
            method = 'GET' if data is None else 'POST'
        rs = requests.request(method, url, data=data, headers=_headers, cookies=cookies,
                              proxies=proxies, timeout=timeout, params=params)
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


def get_category():
    url = 'http://www.supchip.com/'
    # response = requests.get(url=url, headers=default_headers)
    response = fetcher(url=url, return_response=True)
    soup = BeautifulSoup(response.content, 'lxml')
    category_div = soup.find('div', class_='fenlie')
    if category_div:
        category_dict = {}
        try:
            category_type = category_div.find('div', class_='cg_type').find_all('li')
            category_list = category_div.find('div', class_='cg_list').find_all('ul')
            for cat_type, cat_list in zip(category_type, category_list):
                name = (cat_type.get_text(strip=True), cat_type.a['href'])
                cat_list = [[li.get_text(strip=True), li.a['href']] for li in cat_list.find_all('li')]
                category_dict[name] = cat_list
            return category_dict
        except TypeError:
            print "Failed!!"
            return {}
    else:
        return {}
        # for k, v in category_dict.items():
        #     print k[0], k[1]
        #     for x in v:
        #         print x[0], x[1]


def run():
    base_url = 'http://www.supchip.com/'
    # 遍历目录
    for k, v in get_category().items():
        for x in v:
            url = urlparse.urljoin(base_url, x[1])
            try:
                pages = get_pages(url)
                if pages == 0:
                    print "Goods Not Found !!! URL %s" % url
                    return 0
            except:
                print "Goods Not Found !!! URL %s" % url
                return 0
            for page in range(1, pages + 1):
                next_url = url + '&page=%d' % page
                try:
                    for data in get_page_detail(url=next_url, category=[k[0], x[0]]):
                        print data
                except:
                    print "Failed %s" % url


PN2 = 'Hqchip'


def get_pages(url=None):
    try:
        # response = requests.get(url=url, headers=default_headers)
        response = fetcher(url=url, return_response=True)
        soup = BeautifulSoup(response.content, 'lxml')
    except:
        print 'Failed'
    search_num_div = soup.find('div', class_='search_num')
    search_num = box.intval(search_num_div.get_text(strip=True)) if search_num_div else 0
    if search_num:
        pages = int(math.ceil(search_num / 10.0))
        return pages
    else:
        return 0


def get_page_detail(url=None, category=None):
    try:
        # response = requests.get(url=url, headers=default_headers)
        response = fetcher(url=url, return_response=True)
        soup = BeautifulSoup(response.content, 'lxml')
    except:
        print 'Failed'

    goods_div = soup.find('div', class_='shengpin')
    if goods_div:
        goods_list = goods_div.find_all('li')
        for goods in goods_list:
            data = {}
            # goods_sn
            if not goods:
                continue
            gid = goods.attrs['data-gdsid']
            if gid:
                _sn = ('%s-%s' % (gid, PN2)).encode('utf-8')
                data['goods_sn'] = hashlib.md5(_sn).hexdigest()
            else:
                continue
            # category
            data['category'] = category if category else []

            # goods_other_name
            other_name_span = goods.find('span', class_='top_1')
            other_name = other_name_span.get_text(strip=True) if other_name_span else ''
            data['goods_other_name'] = other_name

            # goods_name
            goods_name_span = goods.find_all('span', class_='p_21')
            if goods_name_span:
                goods_name = goods_name_span[1].get_text(strip=True)
                data['goods_name'] = goods_name.split(u'：')[1]
                print data['goods_name']

            # goods_desc
            goods_type_span = goods.find('span', class_='p_21')
            data['goods_desc'] = goods_type_span.get_text(strip=True) if goods_type_span else ''

            # tiered cn_price
            price_span = goods.find('span', class_='p_23')
            hk_price = 0.0
            oversea_price = 0.0
            cn_price = box.floatval(price_span.get_text(strip=True)) if price_span else 0.00
            data['tiered'] = [[1, hk_price, cn_price, oversea_price]]

            # stock
            stock_span = goods.find('span', class_='p_24')
            data['stock'] = box.intval(stock_span.get_text(strip=True)) if stock_span else 0

            # url
            data['url'] = url

            # img
            data['goods_img'] = ''

            yield data


def next_page(page=None, category=None, ):
    """

    :param page: int
    :param category: [k[0], x[1]] 
    :return: dict
    """
    url = 'http://www.supchip.com/search.php'
    default_headers['Referer'] = category[1]

    default_headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    pattern_cid = re.compile(r'id=(\d+)')
    cid = pattern_cid.search(category[1])
    print cid.group(1)
    if u'电容' in category[0]:
        keywords = '%E7%94%B5%E5%AE%B9'
    elif u'电阻' in category[0]:
        keywords = '%E7%94%B5%E9%98%BB'
    else:
        keywords = ''

    if cid and keywords:
        form_data = {
            'page': page,
            'category': cid.group(1),
            'keywords': keywords,
            'act': 'ajax_search',
            'drop_down': 1,
        }
        response = requests.post(url=url, data=form_data, headers=default_headers, allow_redirects=False)
        redirect_url = urlparse.urljoin(url, response.headers.get('location'))
        print response.headers.get('location')
        del default_headers['content-type']
        default_headers['content-length'] = '0'
        data = requests.get(url=redirect_url, headers=default_headers)
        print data.content


if __name__ == "__main__":
    # run()
    for x in get_page_detail(url='http://www.supchip.com/category.php?id=640&page=2', category=[]):
        print x