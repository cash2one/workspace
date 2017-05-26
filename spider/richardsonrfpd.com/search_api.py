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
    # url = 'http://www.richardsonrfpd.com/Pages/home.aspx'
    url = 'http://www.richardsonrfpd.com/Pages/Product-End-Category.aspx?productCategory=10047'
    response = sess.get(url=url, data=form_data, headers=default_headers)
    #
    # print response.status_code
    with open(r'html/productCategory10047.html', 'w') as fp:
        fp.write(response.text.encode('utf-8'))
    #
    # time.sleep(1)
    # with open(r'html/productCategory.html', 'r') as fp:
    #     html = fp.read()

    html = response.text.encode('utf-8')
    root = lxml.html.fromstring(html)




if __name__ == '__main__':
    main()
