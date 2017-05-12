#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11
import hashlib
import sqlite3

setting = {
    'proxy_db': r'proxy.db',
}


# class ProxyDB(object):
#     """
#     单例模式
#     """
#
#     class Proxy_SQLite(object):
#         """数据库操作封装"""
#
#         def __init__(self):
#             self.proxy_db = sqlite3.connect(database=setting.get('proxy_db'), timeout=15)
#
#         def get(self):
#             """ 返回当前实例的 ID，是全局唯一的"""
#             return id(self)
#
#     # 类变量，用于存储 _A 的实例
#     _instance = None
#
#     def __init__(self):
#         """ 先判断类变量中是否已经保存了 _A 的实例，如果没有则创建一个后返回"""
#         if Singleton._instance is None:
#             Singleton._instance = Singleton._A()
#
#     def __getattr__(self, attr):
#         """ 所有的属性都应该直接从 Singleton._instance 获取"""
#         return getattr(self._instance, attr)
def main():
    # proxy_db = sqlite3.connect(database=setting.get('proxy_db'))
    a = hashlib.md5("ip+data")
    print a.hexdigest()
    print len(a.hexdigest())
    print 2**16
    import time
    print len(str(int(time.time())))
    print str(int(time.time()))


if __name__ == '__main__':
    main()
