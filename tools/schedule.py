#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import subprocess


def main():
    sb = subprocess.call(['python', r'E:\workspace\tools\fetch_proxies.py', '-r'])
    print sb


if __name__ == '__main__':
    main()
