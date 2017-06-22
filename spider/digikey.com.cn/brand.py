#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/21

import re
import time
import json
import lxml.html
import requests
import threading
from tools import box as util

DEFAULT_HEADERS = {
    'Host': 'www.digikey.com.cn',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36'
}

CRAWL_LOCK = threading.Lock()
SUPPLIER_INDEX = []
RETRY_LIST = []
RESULTS = []


def get_index():
    index_page = 'http://www.digikey.com.cn/zh/supplier-centers'
    rs = requests.get(url=index_page, headers=DEFAULT_HEADERS)
    _urls = re.findall(r'"Link":"([^"]+)"', rs.text.encode('utf-8'))
    if _urls:
        _urls = [util.urljoin(index_page, x) for x in _urls]
        return _urls


class Crawl(threading.Thread):
    def run(self):
        while SUPPLIER_INDEX:
            crawl_brand()


def crawl_brand(url=None):
    global SUPPLIER_INDEX
    global RETRY_LIST
    global RESULTS
    CRAWL_LOCK.acquire()
    target = SUPPLIER_INDEX.pop() if not url else url
    CRAWL_LOCK.release()

    try:
        rs = requests.get(url=target, headers=DEFAULT_HEADERS, timeout=20)
        time.sleep(0.3)
        if rs.status_code in [404, 403, 400]:
            return None
    except Exception as e:
        print "PUT INTO RETRY LIST: ", target
        CRAWL_LOCK.acquire()
        RETRY_LIST.append(target)
        CRAWL_LOCK.release()
        return None
    root = lxml.html.fromstring(rs.text)
    _name = root.xpath('//td[@class="supplier-description"]/h1')
    supplier_name = _name[0].text if _name else ''
    if supplier_name is None or not supplier_name.strip():
        print "PARSE ERROR, STATUS CODE {code}, RETRY: {url}".format(code=rs.status_code, url=target)
        if rs.status_code in [500, 503, 504]:
            CRAWL_LOCK.acquire()
            RETRY_LIST.append(target)
            CRAWL_LOCK.release()
        elif rs.status_code == 200:
            CRAWL_LOCK.acquire()
            with open(r'error_{flag}.html'.format(flag=target.split('/')[-1]), 'w') as fp:
                fp.write(rs.text.encode('utf-8'))
            CRAWL_LOCK.release()
        return None
    _img = root.xpath('//td[@class="supplier-logo"]//img/@src')
    supplier_logo = util.urljoin(target, _img[0]) if _img else ''

    _description = root.xpath('//td[@class="supplier-description"]/p')
    supplier_description = _description[0].text_content().strip() if _description else ''
    brand = {
        'name': supplier_name,
        'img': supplier_logo,
        'desc': supplier_description,
    }
    CRAWL_LOCK.acquire()
    RESULTS.append(brand)
    CRAWL_LOCK.release()
    print brand
    return brand


class Save(threading.Thread):
    def run(self):
        while SUPPLIER_INDEX or RETRY_LIST:
            save_result()
        else:
            data_str = json.dumps(RESULTS)
            with open(r'supplier_info.html', 'a') as fp:
                fp.write(data_str + '\n')


def save_result():
    global RESULTS
    if len(RESULTS) >= 100:
        data_str = json.dumps(RESULTS)
        with open(r'supplier_info.html', 'a') as fp:
            fp.write(data_str + '\n')
        RESULTS = []


def main():
    global SUPPLIER_INDEX
    SUPPLIER_INDEX = get_index()

    task_list = []
    for x in range(10):
        task = Crawl()
        task.start()
        time.sleep(0.3)
        task_list.append(task)

    # Save().start()

    for task in task_list:
        task.join()

    retry = 3
    global RETRY_LIST
    while RETRY_LIST:
        url = RETRY_LIST.pop()
        rs = crawl_brand(url)
        time.sleep(1)
        if rs is not None:
            retry = 3
        elif retry > 0:
            RETRY_LIST.append(url)
            retry -= 1
        else:
            continue


if __name__ == '__main__':
    main()
