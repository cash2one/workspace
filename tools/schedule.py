#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import db
import subprocess


def main():
    # sb = subprocess.call(['python', r'E:\workspace\tools\fetch_proxies.py', '-r'])
    proxy_db = db.ProxyDB()
    condition = {
        'proxy_port': {'eq': '808'},
        'proxy_protocol': 'HTTPS'
    }
    for x in proxy_db.get_iter(table='proxies', condition=condition, limit=10, fields=('proxy_protocol', 'proxy_ip', 'proxy_port')):
        print x


if __name__ == '__main__':
    main()
