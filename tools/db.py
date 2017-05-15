#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import config
import sqlite3

db_setting = config.DB


def dict_to_str(data=None, joiner=','):
    """字典类型拼接成字符串
    将字典的键和值分别连成字符串放到列表中返回
    :param joiner: ','
    :param data: dict
    :return: list
    """
    key_tuple, value_tuple = '', ''
    sql_dict = dict()
    if isinstance(data, dict):
        for k, v in data.items():
            key_tuple += k + joiner
            if not isinstance(v, (str, unicode)):
                value_tuple += str(v) + joiner
            else:
                value_tuple += repr(v.encode('utf-8')) + joiner
        else:
            # 去除最后多出来的逗号
            key_tuple = key_tuple[:-1]
            value_tuple = value_tuple[:-1]

        key_tuple = '(' + key_tuple + ')'
        value_tuple = '(' + value_tuple + ')'
        return [key_tuple, value_tuple]


class ProxyDB(object):
    """
    单例模式
    """
    # TODO 添加异常数据的判断和异常处理
    class Proxy_SQLite(object):
        """数据库操作封装"""

        def __init__(self):
            self.proxy_db = sqlite3.connect(database=db_setting.get('proxy_db'), timeout=15)

        def display(self):
            return id(self)

        def get_fields(self, table_name):
            """
            获取字段列表
            """
            result = self.proxy_db.execute('PRAGMA table_info({table_name});'.format(table_name=table_name))
            info = []
            if result:
                for val in result:
                    if isinstance(val, dict):
                        f = val['Field']
                    else:
                        f = val[0]
                    if isinstance(f, unicode):
                        f = f.encode('utf-8')
                    info.append(f)
            return info

        def is_exist(self, table='', key=''):
            """是否存在
            检查是否已经存在相同的元素
            :param table: 表名 
            :param key: id
            :return: bool
            """
            cursor, result = None, None
            if table and key:
                sql_str = """SELECT id FROM {TABLE_NAME} WHERE id={key}""".format(TABLE_NAME=table, key=repr(key))
                cursor = self.proxy_db.execute(sql_str)
                result = cursor.fetchall()
            return result

        # 字典类型或列表类型整理为sql字符串
        # TODO 添加插入条件功能
        def insert(self, table, data=None, return_insert_id=False):
            """插入数据
            可以直接插入字典类型或列表(元组)类型数据到指定表
            :param table: 表名
            :param data: dict 或 list
            :param return_insert_id: 
            :return: 
            """
            sql_str = ''
            if isinstance(data, dict):
                data_str = dict_to_str(data)
                sql_str = """INSERT INTO {TABLE_NAME} {COLUMN_NAME} VALUES {VALUES}""".format(TABLE_NAME=table,
                                                                                              COLUMN_NAME=data_str[0],
                                                                                              VALUES=data_str[1])
            elif isinstance(data, list):
                data_str = '(' + ','.join(data) + ')'
                sql_str = """INSERT INTO {TABLE_NAME} VALUES {VALUES}""".format(TABLE_NAME=table, VALUES=data_str)

            self.proxy_db.execute(sql_str)
            self.proxy_db.commit()

        def close(self):
            self.proxy_db.close()

    # 类变量，用于存储数据库的实例
    _instance = None

    def __init__(self):
        """ 先判断类变量中是否已经保存了 _A 的实例，如果没有则创建一个后返回"""
        if ProxyDB._instance is None:
            ProxyDB._instance = ProxyDB.Proxy_SQLite()

    def __getattr__(self, attr):
        """ 所有的属性都应该直接从 Singleton._instance 获取"""
        return getattr(self._instance, attr)


# class Singleton(object):
#     """
#     最简单的单例模式
#     """
#
#     class _A(object):
#         """
#        真正干活的类, 对外隐藏
#         """
#
#         def __init__(self):
#             pass
#
#         def display(self):
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


if __name__ == '__main__':
    # pd = ProxyDB()
    # print pd.display()
    d = {'key1': "hell", 'key2': 3}
    l = dict_to_str(d)
    for x in l:
        print repr(x)