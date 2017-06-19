#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/9

import Queue
import requests
import threading

DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
}

setting = {
    'china.rs-online.com': {
        'headers': {},
        'cookies': {},
    }
}


class Downloader(threading.Thread):
    def run(self):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
