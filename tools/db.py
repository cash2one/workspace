#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import config
import sqlite3
import logging

db_logger = logging.getLogger('DB')

db_setting = config.DB

# 参考mongo的查询方法将sql条件查询统一
SQL_OPERATOR = {'eq': '=', 'ne': '!=', 'gt': '>', 'gte': '>=', 'lt': '<', 'let': '<=', 'like': 'LIKE',
                'in': 'IN', '!like': 'NOT LIKE', '!in': 'NOT IN', }


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
            if isinstance(v, unicode):
                value_tuple += repr(v.encode('utf-8')) + joiner
            else:
                value_tuple += repr(v) + joiner
        else:
            # 去除最后多出来的逗号
            key_tuple = key_tuple[:-1]
            value_tuple = value_tuple[:-1]

        key_tuple = '(' + key_tuple + ')'
        value_tuple = '(' + value_tuple + ')'
        return [key_tuple, value_tuple]


# 临时方法， 方法局限性无法嵌套多层操作符
# TODO 通过递归的方法重写方法
def mongo_interface_to_sql(condition=None):
    condition = condition if condition else {}
    global SQL_OPERATOR
    operator = SQL_OPERATOR
    operation = []
    if isinstance(condition, dict):
        for k, v in condition.items():
            if isinstance(v, dict):
                if len(v) != 1:
                    db_logger.debug(u"条件语句语法不正确！参考mongo查询语法")
                    return None
                # 取出操作符和值
                v_key, v_value = v.popitem()
                # 将操作符小写
                v_key = v_key.lower()
                operation.append(k + operator[v_key] + repr(v_value))
            elif isinstance(v, list):
                if k != 'or' and len(v) < 2:
                    db_logger.debug(u"条件语句语法不正确！只有or的值才可以是列表")
                    return None
                temp_list = []
                print v
                for inner_dict in v:
                    print inner_dict
                    if len(inner_dict) != 1:
                        db_logger.debug(u"条件语句语法不正确！参考mongo查询语法")
                        return None
                    # 取出操作符和值
                    v_key, v_value = inner_dict.popitem()
                    # 将操作符小写
                    v_key = v_key.lower()
                    if isinstance(v_value, dict):
                        v_key_key, v_value_value = v_value.popitem()
                        temp_operation = v_key + operator[v_key_key] + repr(v_value_value)
                    else:
                        temp_operation = v_key + '=' + repr(v_value)
                    temp_list.append(temp_operation)
                operation.append('({or_statement})'.format(or_statement=' OR '.join(temp_list)))
            else:
                operation.append(k + '=' + repr(v))
            print operation
    operator_str = ' AND '.join(operation) if operation else None
    return operator_str


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

        # AND 和 OR 的使用和Mongo的一致
        def select(self, table='', fields=None, condition=None, limit=10):
            """
            使用mongo查询方式来查询SQL
            :param table: 表名
            :param fields: 需要输出的数据域 元组或列表格式
            :param condition: {'proxy_port': {'eq': '808'}, 'proxy_high_quality': 1}} 
                         ==>> proxy_port = '808' and proxy_high_quality = 1
                         {'proxy_ip': {'eq': '192.168.1.1'}, 'OR':[{'proxy_protocol':'HTTP'}, {'proxy_protocol':'HTTPS'}]}
                         ==>> proxy_ip = '192.168.1.1' AND (proxy_protocol = 'HTTP' OR proxy_protocol = 'HTTPS')
            :param limit: 需要输出的数据数目 整型
            :return: list
            """
            if not table:
                return None
            fields = ','.join(fields) if isinstance(fields, (list, tuple)) else '*'
            condition_str = mongo_interface_to_sql(condition) if isinstance(condition, dict) else None
            condition_str = """ WHERE {CONDITION}""".format(CONDITION=condition_str) if condition_str else ''
            limit_str = """ LIMIT {LIMIT}""".format(LIMIT=limit) if limit else ''
            sql_str = """SELECT {COLUMNS} FROM {TABLE_NAME}{condition}{limit}""".format(
                COLUMNS=fields,
                TABLE_NAME=table,
                condition=condition_str,
                limit=limit_str)
            cursor = self.proxy_db.execute(sql_str)
            return cursor

        def get_list(self, **kwargs):
            cursor = self.select(table=kwargs.get('table', ''), condition=kwargs.get('condition', None),
                                 limit=kwargs.get('limit', 10), fields=kwargs.get('fields', None))
            return cursor.fetchall() if cursor else None

        def get_iter(self, **kwargs):
            cursor = self.select(table=kwargs.get('table', ''), condition=kwargs.get('condition', None),
                                 limit=kwargs.get('limit', 10), fields=kwargs.get('fields', None))
            while True and cursor:
                row = cursor.fetchone()
                if not row:
                    break
                yield row

        # 字典类型或列表类型整理为sql字符串
        # TODO 添加插入条件功能
        def insert(self, table='', data=None, return_insert_id=False):
            """插入数据
            可以直接插入字典类型或列表(元组)类型数据到指定表
            :param table: 表名
            :param data: dict 或 list
            :param return_insert_id: 
            :return: 
            """
            sql_str = ''
            if not table or not data:
                return None
            if isinstance(data, dict):
                data_str = dict_to_str(data)
                sql_str = """INSERT INTO {TABLE_NAME} {COLUMN_NAME} VALUES {VALUES}""".format(TABLE_NAME=table,
                                                                                              COLUMN_NAME=data_str[0],
                                                                                              VALUES=data_str[1])
            elif isinstance(data, list):
                data = [repr(x) for x in data]
                data_str = '(' + ','.join(data) + ')'
                sql_str = """INSERT INTO {TABLE_NAME} VALUES {VALUES}""".format(TABLE_NAME=table, VALUES=data_str)

            self.proxy_db.execute(sql_str)
            self.proxy_db.commit()

        def close(self):
            self.proxy_db.close()

        def __del__(self):
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

    d = {"proxy_ip": {'eq': '127.0.0.1'}, 'or': [{"proxy_port": "808"}, {"proxy_alive": 1}]}
    print mongo_interface_to_sql(d)
