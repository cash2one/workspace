#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import time
import json
import Queue
import os.path
import logging
import requests
import threading
import ConfigParser

from requests import ConnectTimeout, ConnectionError, ReadTimeout

# 日志输出
_logger = logging.getLogger('worker')
_logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
s_handler = logging.StreamHandler()
s_handler.setFormatter(fmt)
_logger.addHandler(s_handler)

# 获取当前所在文件夹路径
APP_ROOT = os.getcwd()
# 检查配置文件是否存在
CONFIG_PATH = os.path.join(APP_ROOT, 'main.config')
if os.path.exists(CONFIG_PATH) is False:
    _logger.info(u'缺少程序主配置文件main.config, 请在服务器http://server/config下载')
    time.sleep(1)
    sys.exit(0)
# 加载配置文件
config = ConfigParser.ConfigParser()
config.read('main.config')
# 读取配置文件中的TASK_API
TASK_API = config.get("worker", "TASK_API")
TASK_QUEUE = Queue.Queue(30)
RETRY_QUEUE = Queue.Queue(30)
DOWNLOADED = Queue.Queue(90)


def get_task():
    # 从接口获取下载任务
    task_api = TASK_API
    task = {}
    try:
        rs = requests.get(url=task_api, timeout=30)
        task = json.loads(rs.text)
    except (ConnectTimeout, ConnectionError, ReadTimeout):
        _logger.debug(u"访问超时，获取下载任务失败, 请检查与服务器的连接。")
    # 将任务放入任务队列]
    if task:
        TASK_QUEUE.put(task)
        return True
    else:
        return None


def download(task, **kwargs):
    # 从队列获取下载任务
    task = task if task else {}
    # 获取下载目标
    target = task.get('download', None)
    if target is None:
        return None
    # 获取控制配置
    control = task.get('control', {})
    upload_path = control.get('upload', None)
    try:
        rs = requests.get(**target)
        downloaded = {
            'content': rs.text,
        }
        if upload_path is not None:
            downloaded.update({'upload': upload_path, 'url': target.get('url')})
        DOWNLOADED.put(downloaded)
        _logger.info(u"下载成功 URL: {url}".format(url=target.get('url')))
        return True
    except Exception as e:
        _logger.debug(u"下载失败放入重试列表 URL: {url}".format(url=target.get('url')))
        # 如果已经携带了retry参数，则不重复添加到重试队列
        if not kwargs.get('retry', False):
            RETRY_QUEUE.put(task)
        return None


def upload(data):
    try:
        upload_path = data.get('upload', None)
        if upload_path is not None:
            post_data = {
                'content': data.get('content', ''),
            }
            rs = requests.post(url=upload_path, data=post_data)
            if rs.status_code == 200:
                _logger.info(u'成功上传 URL: {url}'.format(url=data.get('url')))
                return True
    except (ConnectionError, ConnectTimeout, ReadTimeout):
        _logger.debug(u"访问超时，上传下载结果失败 请检查与服务器的连接。")
        return False


class TaskProducer(threading.Thread):
    def run(self):
        while True:
            get_task()
            time.sleep(0.2)


class DownloadConsumer(threading.Thread):
    def run(self):
        while True:
            task = TASK_QUEUE.get()
            TASK_QUEUE.task_done()
            download(task)


class RetryConsumer(threading.Thread):
    def run(self):
        while True:
            task = RETRY_QUEUE.get()
            ok = download(task)
            retry = 2
            while not ok and retry:
                ok = download(task, retry=retry)
                retry -= 1


class Uploader(threading.Thread):
    def run(self):
        while True:
            downloaded = DOWNLOADED.get()
            DOWNLOADED.task_done()
            ok = upload(downloaded)
            retry = 2
            while not ok and retry:
                ok = upload(downloaded)
                retry -= 1


def main():
    # 启动一个任务获取器
    TaskProducer().start()

    # 启动七个下载器
    for x in range(7):
        DownloadConsumer().start()

    # 启动一个重试下载器
    RetryConsumer().start()

    # 启动一个上传器
    Uploader().start()

    # while True:
    #     time.sleep(5)
    #     print 'DOWNLOADED', DOWNLOADED.qsize()
    #     print 'TASK_QUEUE', TASK_QUEUE.qsize()
    #     print 'RETRY_QUEUE', RETRY_QUEUE.qsize()


if __name__ == '__main__':
    main()
