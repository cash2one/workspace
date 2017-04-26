#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/4/26


import time
import sys
import signal

"""
1、使用多线程
2、使用信号 以下使用的方法
3、使用 KeyboardInterrupt
"""

loop = True


def int_loop(signum, frame):
    print("set loop false")
    frame.f_globals['loop'] = False
    print signum
    print dir(frame)
    with open("graceful.txt", 'w') as fp:
        fp.write('999')


signal.signal(signal.SIGINT, int_loop)

while loop:
    print "1"

print("sleep finished")
