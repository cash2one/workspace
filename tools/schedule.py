#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import db
import subprocess


def main():
    # sb = subprocess.call(['python', r'E:\workspace\tools\fetch_proxies.py', '-r'])
    proxy_db = db.ProxyDB()
    test_data = {
        'proxy_port': {'eq': '8080'},
        'proxy_protocol': 'HTTPS'
    }
    print proxy_db.select(table='proxies', data=test_data, limit=10, fields=('proxy_protocol', 'proxy_ip', 'proxy_port'))


if __name__ == '__main__':
    main()
