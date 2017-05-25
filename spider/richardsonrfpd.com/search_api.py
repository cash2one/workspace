#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/24

import copy
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
    response = sess.get(url=url, data=form_data, headers=default_headers)

    # print response.status_code
    # with open(r'html/search_result.html', 'w') as fp:
    #     fp.write(response.text.encode('utf-8'))
    # with open(r'html/search_result.html', 'r') as fp:
    #     html = fp.read()

    html = response.text.encode('utf-8')
    root = lxml.html.fromstring(html)

    # make form data
    try:
        input_list = root.xpath('//input[@type="hidden"]')
        for input_box in input_list:
            attr = input_box.attrib
            key = attr.get('name', None)
            if key is not None:
                form_data[str(key)] = str(attr.get('value', ''))
        form_data.update({'ctl00$Search$txtboxPNSearch': 'TGA4042',})
    except (IndexError, AttributeError):
        print "omega"
        raise
    _headers = copy.copy(default_headers)
    _headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
    })
    response = sess.get(url=url, headers=_headers)
    print response.status_code




if __name__ == '__main__':
    main()
