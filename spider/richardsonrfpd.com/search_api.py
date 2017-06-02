#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/24

import re
import math
import json
import copy
import time
import urlparse
import requests
import lxml.html

from tools import box as util

headers_string = """Host: www.richardsonrfpd.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Referer: http://www.richardsonrfpd.com/Pages/home.aspx
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
"""

default_headers = util.headers_to_dict(headers_str=headers_string)
print default_headers


def get_event_kwargs(response=None, **kwargs):
    """获取网页中隐藏表单的值
    返回整理好的触发事件需要的表单数据字典
    :param response: 请求网页返回的对象
    :param kwargs: 其他的需要加入时间表单的键值对
    :return: 字典
    """
    html = kwargs.pop('html', None)
    if response is None and html is None:
        return -400
    try:
        html = response.text.encode('utf-8') if response else html
        root = lxml.html.fromstring(html)
    except:
        return -400
    event_data = {}
    # 获取事件参数 __VIEWSTATE
    field1 = root.xpath('//input[@id="__VIEWSTATE"]/@value')
    event_data['__VIEWSTATE'] = field1[0] if field1 else ''

    # 获取事件参数 __VIEWSTATEGENERATOR
    field2 = root.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')
    event_data['__VIEWSTATEGENERATOR'] = field2[0] if field2 else ''

    # 获取事件参数 __VIEWSTATEENCRYPTED 没有这个参数请求会出错
    event_data['__VIEWSTATEENCRYPTED'] = ''

    # 获取事件参数 __EVENTVALIDATION
    field3 = root.xpath('//input[@id="__EVENTVALIDATION"]/@value')
    event_data['__EVENTVALIDATION'] = field3[0] if field3 else ''
    event_data.update(kwargs)
    return event_data


def do_search(response=None, keyword=''):
    if response is None:
        return -400
    form_data = {}
    event_data = get_event_kwargs(response)
    sess = requests.session()
    # 搜索事件 表单构造
    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$txtPartNumber'] = keyword
    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$ctl03'] = 'Starts with'
    form_data['ctl00$SPWebPartManager1$g_096ee875_b50a_46d8_828c_52a9076a775d$btnSearch'] = 'Search'
    form_data.update(event_data)

    _headers = copy.copy(default_headers)
    _headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        result_response = sess.post(url=response.url, headers=_headers, data=form_data)
        with open(r'html/search_result_no_detail.html', 'w') as fp:
            fp.write(result_response.text.encode('utf-8'))
    except:
        return -400
    # 显示所有搜索
    if 'Search-Results.aspx' in result_response.url:
        root = lxml.html.fromstring(result_response.text.encode('utf-8'))
        product_table = root.xpath('//table[@class="PSTable"]')
        if product_table:
            return result_response
        form_data = {'__EVENTTARGET': 'ctl00$SPWebPartManager1$g_539e9434_3497_4d6a_badc_24c5f583680c$btnBottomShowAll'}
        event_data = get_event_kwargs(result_response)
        form_data.update(event_data)
        _headers.update({'Referer': result_response.url})
        try:
            resp = sess.post(url=result_response.url, headers=_headers, data=form_data, allow_redirects=False)
            return resp
        except:
            return -400
    elif 'Product-Details' in result_response.url:
        return result_response


def main():
    form_data = {}
    # sess = requests.session()
    url = 'http://www.richardsonrfpd.com/Pages/AdvanceSearch.aspx'
    # url = 'http://www.richardsonrfpd.com/Pages/Product-End-Category.aspx?productCategory=10047'
    # response = sess.get(url=url, data=form_data, headers=default_headers)
    #
    # print response.status_code
    # with open(r'html/AdvanceSearch.html', 'w') as fp:
    #     fp.write(response.text.encode('utf-8'))
    #
    # time.sleep(1)
    with open(r'html/search_result_show_all.html', 'r') as fp:
        html = fp.read()
    # resp = do_search(response, 'ANT')
    # product_list
    root = lxml.html.fromstring(html)
    product_id = root.xpath('//table[@class="PSTable"]/@id')
    product_id = product_id[0] if product_id else None
    product_list = root.xpath('//a[starts-with(@id, {pid})]'.format(pid=repr(product_id)))
    print product_list[0].text.strip()
    product_list = root.xpath('//a[starts-with(@id, {pid})]/@href'.format(pid=repr(product_id)))
    print product_list
    base_url = 'http://www.richardsonrfpd.com/Pages/Search-Results.aspx'
    product_list = [urlparse.urljoin(base_url, x) for x in product_list]
    print product_list
    print '-------------------'
    # with open(r'html/search_result_show_all.html', 'w') as fp:
    #     fp.write(resp.text.encode('utf-8'))
    with open(r'html/productCategory=10374page1.html', 'r') as fp:
        html = fp.read()
    event = get_event_kwargs(html=html)
    print event



if __name__ == '__main__':
    main()
