#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/17

import requests

filter_rules={
    r'/products/[^/]+',  # index page
    r'/parametric/',  # second page
}

default_headers = {
    'Host': 'shopping.netsuite.com',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f'}


def main():
    # index_page = 'http://www.linear.com.cn/products/'
    # response = requests.get(url=index_page, headers=default_headers)
    # with open(r'html/index.html', 'w') as fp:
    #     fp.write(response.text.encode('utf-8'))
    # second_page = 'http://www.linear.com.cn/products/IF_Amplifiers_%7C_ADC_Drivers'
    # response = requests.get(url=second_page, headers=default_headers)
    # with open(r'html/second_page.html', 'w') as fp:
    #     fp.write(response.text.encode('utf-8'))
    product_list_page = 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f'
    response = requests.get(url=product_list_page, headers=default_headers)
    with open(r'html/product_list_page.html', 'w') as fp:
        fp.write(response.text.encode('utf-8'))

if __name__ == '__main__':
    main()
