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


def main():
    form_data = {}
    sess = requests.session()
    url = 'http://www.richardsonrfpd.com/Pages/home.aspx'
    # url = 'http://www.richardsonrfpd.com/Pages/Product-End-Category.aspx?productCategory=10047'
    response = sess.get(url=url, data=form_data, headers=default_headers)
    #
    # print response.status_code
    with open(r'html/home.html', 'w') as fp:
        fp.write(response.text.encode('utf-8'))
    #
    # time.sleep(1)
    # with open(r'html/home.html', 'r') as fp:
    #     html = fp.read()

    html = response.text.encode('utf-8')
    root = lxml.html.fromstring(html)

    # 获取事件参数 ctl00$scr
    match = re.search(r'(ctl00[^\"\',]+outerPanelPanel)', html)
    src = match.group() + '|' if match else ''

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

    html = response.text.encode('utf-8')
    root = lxml.html.fromstring(html)


if __name__ == '__main__':
    main()
