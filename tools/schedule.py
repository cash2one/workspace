#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import db
import time
import Queue
import threading
import subprocess

import os.path
import tools.db
import time
import Queue
import random
import threading
import requests
import config
import logging
import subprocess
from requests.exceptions import ProxyError, ConnectionError, ConnectTimeout, ReadTimeout

proxy_schedule = logging.getLogger("proxy_schedule")
proxy_schedule.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
s_handler = logging.StreamHandler()
s_handler.setFormatter(fmt)
proxy_schedule.addHandler(s_handler)

# 校验队列
PROXY_QUEUE = Queue.Queue(30)
# 线程锁
PROXY_LOCK = threading.Lock()
# 默认的请求头
default_headers = config.DEFAULT_HEADERS
alive_proxies_list = []


class ProxiesProducer(threading.Thread):
    def run(self):
        fill_proxy_queue()


def fill_proxy_queue():
    global PROXY_QUEUE
    proxy_db = tools.db.ProxyDB()
    app_path = os.path.join(config.APP_ROOT, 'tools', 'fetch_proxies.py')
    try:
        # 是否已经执行过fetch_proxy
        exit_code = 1
        while True:
            proxies_iter = proxy_db.get_iter(
                table='proxies',
                condition=None,
                limit=None,
                fields=('proxy_ip', 'proxy_port', 'proxy_protocol', 'proxy_support_https'),
            )
            for proxy in proxies_iter:
                PROXY_QUEUE.put(proxy)
                proxy_schedule.debug("PROXY_QUEUE size is {qsize}".format(qsize=PROXY_QUEUE.qsize()))
            else:
                # 一个小时全站抓取一次代理
                if not exit_code:
                    proxy_schedule.debug("Run fetch more proxy after 1 hours")
                    time.sleep(60 * 60)
                # 先清空旧数据
                proxy_db.delete(table='proxies', confirm=True)
                time.sleep(1)
                # 开启爬虫抓取新的代理
                exit_code = subprocess.call(['python', app_path, '-r'])
                proxy_schedule.debug("Finish fetch_proxies, proxy test go on...")
                time.sleep(1)
                # 遍历完成之后就重新抓取

    except (KeyboardInterrupt, SystemExit):
        del proxy_db


class ProxyRequestTester(threading.Thread):
    def run(self):
        global alive_proxies_list
        while True:
            proxy = PROXY_QUEUE.get()
            PROXY_QUEUE.task_done()
            target = "http://www.baidu.com/index.html"
            proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[0], port=proxy[1], protocol=proxy[2])
            proxies = {
                'id': proxy[0],
                'proxies': {
                    'http': proxy_url,
                    'https': proxy_url,
                }
            }
            # 访问异常说明代理无效
            try:
                response = requests.head(url=target, headers=default_headers, proxies=proxies, timeout=5)
                # 如果能正常获取头部信息说明代理存活，放入全局变量alive_proxies_list
                if response.status_code == 200:
                    # print response.headers
                    # 写文件列表
                    PROXY_LOCK.acquire()
                    # proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[1], port=proxy[2], protocol=proxy[3])
                    alive_proxies_list.append(proxy)
                    proxy_schedule.debug("alive_proxies_list size is {size}".format(size=len(alive_proxies_list)))
                    PROXY_LOCK.release()
            except (ProxyError, ConnectionError, ConnectTimeout, ReadTimeout):
                continue


class ProxySaver(threading.Thread):
    def run(self):
        insert_into_db()


def insert_into_db():
    global alive_proxies_list
    database = config.DB.get('alive_db', None)
    if not database:
        return None
    proxy_saver = tools.db.SQLite(database=database)
    while True:
        clear_mark = False
        # 每天零点清空当天的存活代理
        midnight = 86400
        now = time.time() % 86400
        # 零点前一秒
        if midnight - now <= 1:
            clear_mark = True
        if len(alive_proxies_list) >= 100 and not clear_mark:
            PROXY_LOCK.acquire()
            proxy_saver.insert(table='alive', data=alive_proxies_list,
                               column=('proxy_ip', 'proxy_port', 'proxy_protocol', 'proxy_support_https'))
            alive_proxies_list = []
            PROXY_LOCK.release()
        if clear_mark:
            proxy_saver.delete(table='alive', confirm=True)
            proxy_schedule.debug("时间:{date} 清空代理数据".format(date=time.ctime(time.time())))
            # 等待2秒，避免重复清空数据
            time.sleep(2)


def db_exit():
    # 检查数据库是否存在不存在则创建数据库
    proxy_db_path = config.DB.get('proxy_db')
    alive_db_path = config.DB.get('alive_db')
    if not os.path.exists(proxy_db_path):
        proxy_db = tools.db.SQLite(database=proxy_db_path)
        table_proxy_ddl = """CREATE TABLE proxies(id CHAR(32) PRIMARY KEY,proxy_ip CHAR(15) NOT NULL,proxy_port VARCHAR(6) NOT NULL,proxy_protocol CHAR(6) NOT NULL,proxy_fetch_date CHAR(16) NOT NULL,proxy_from TEXT NOT NULL,proxy_location TEXT,proxy_support_https INT)"""
        proxy_db.create(ddl=table_proxy_ddl)
        proxy_db.close()
        del proxy_db

    if not os.path.exists(alive_db_path):
        alive_db = tools.db.SQLite(database=alive_db_path)
        table_alive_ddl = """CREATE TABLE alive(id INTEGER PRIMARY KEY AUTOINCREMENT,proxy_ip CHAR(15) NOT NULL,proxy_port VARCHAR(6) NOT NULL,proxy_protocol CHAR(6) NOT NULL,proxy_support_https INT)"""
        alive_db.create(ddl=table_alive_ddl)
        alive_db.close()
        del alive_db


def main():
    # 检查数据库是否存在不存在则创建数据库
    db_exit()
    # 启动一个从数据库获取代理的生产者
    ProxiesProducer().start()
    # 启动十个测试代理的消费者
    for x in range(10):
        ProxyRequestTester().start()
    # 启动一个保存有效代理的消费者
    ProxySaver().start()

    # 将验证过的代理存储起来
    global alive_proxies_list

    while True:
        # 存活的代理列表长度超过100记录
        if len(alive_proxies_list) > 30 and int(time.time()) % 30 == 0:
            file_path = os.path.join(config.APP_ROOT, 'db', 'alive.txt')
            _top_30 = alive_proxies_list[:30]
            with open(file_path, 'w') as fp:
                for proxy in _top_30:
                    proxy_url = "{protocol}://{ip}:{port}".format(ip=proxy[0], port=proxy[1], protocol=proxy[2])
                    fp.write(proxy_url + '\n')


##################################################
# 最简单的生产者消费者模式
queue = Queue.Queue(10)


# 生产者
class Producer(threading.Thread):
    def run(self):
        while True:
            elem = random.randrange(100)
            queue.put(elem)
            print "Producer a elem {}, Now size is {}".format(elem, queue.qsize())
            time.sleep(random.random())


# 消费者
class Consumer(threading.Thread):
    def run(self):
        while True:
            elem = queue.get()
            queue.task_done()
            print "Consumer a elem {}. Now size is {}".format(elem, queue.qsize())
            time.sleep(random.random())


##################################################

if __name__ == '__main__':
    main()