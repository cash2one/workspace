#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/8
import requests
from urllib import quote
import urlparse
from tools import box

headers = """
accept:application/json, text/javascript, */*; q=0.01
accept-encoding:gzip, deflate, br
accept-language:en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
cache-control:no-cache
content-length:0
origin:https://www.maximintegrated.com
pragma:no-cache
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36
x-requested-with:XMLHttpRequest"""
headers = box.headers_to_dict(headers)


def main(keyword=''):
    keyword = "MAX6389XS44D3+T"
    url = 'https://www.maximintegrated.com/en/search/wsi/parts.ajax?pn={keyword}'.format(keyword=quote(keyword))
    # url = "https://www.maximintegrated.com/bin/productsearch?sp_q={keyword}&q={keyword}".format(keyword=keyword)
    resp = requests.get(url=url, headers=headers)
    print resp.text.encode('utf-8')

if __name__ == '__main__':
    main()
