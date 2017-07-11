#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/27

import os
import sys
import time
import json
import os.path
import logging
import requests
import urlparse
import threading
import subprocess
import ConfigParser
from requests import ConnectTimeout, ConnectionError, ReadTimeout

_logger = logging.getLogger('updater')
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
config.read(CONFIG_PATH)
# 服务器更新地址
UPDATE_URL = config.get('update', 'UPDATE_URL')
UPDATE_TYPE = config.get('update', 'UPDATE_TYPE').split(',')


def get_file_dict(root):
    """获取所在目录的文件列表"""
    if root is None:
        return None
    file_dict = dict()
    for path, dirs, files in os.walk(root, True, None):
        # 设置检索深度为3
        depth = path.replace(root, '').split('\\')[1:]
        if len(depth) >= 4:
            break
        for f in files:
            file_name, suffix = os.path.splitext(f)
            if suffix not in UPDATE_TYPE:
                continue
            file_path = os.path.join(path, f)
            create_time = os.stat(file_path).st_mtime
            file_dict.update({f: {'file_path': file_path, 'create_time': int(create_time)}})
    return file_dict


def get_update_info(update_url=None):
    """从服务器获取需要更新的文件列表, 更新程序退出"""
    if update_url is None:
        return None
    try:
        update_info = requests.get(url=update_url, timeout=20)
        return json.loads(update_info.text)
    except (ConnectTimeout, ConnectionError, ReadTimeout):
        _logger.debug(u"获取更新数据超时, 请检查与服务器的连接。程序正在退出...")
        time.sleep(1)
        sys.exit(0)


def compare_files(file_dict=None, update_info=None):
    """对比本地文件和服务器文件列表，生成更新文件，若无需更新文件则返回None，更新程序退出"""
    if file_dict is None or not isinstance(file_dict, dict):
        return None
    if update_info is None or not isinstance(update_info, dict):
        return None

    update_list = list()
    for file_name, file_info in update_info.items():
        create_time_server = file_info.get('create_time')
        file_in_local = file_dict.get(file_name, None)
        if file_in_local is None:
            file_path = os.path.join(APP_ROOT, file_name)
            update_list.append([file_path, urlparse.urljoin(UPDATE_URL, file_name)])
        else:
            create_time_local = file_in_local.get('create_time')
            if create_time_server - create_time_local > 0:
                update_list.append([file_in_local.get('file_path'), urlparse.urljoin(UPDATE_URL, file_name)])
    return update_list if update_list else None


def updating(update_list=None):
    """遍历更新列表更新文件"""
    if update_list is None or not isinstance(update_list, list):
        _logger.info(u"程序已经更新到最新，更新程序正在退出...")
        time.sleep(1)
        sys.exit(0)
    # 关闭worker的进程
    command = 'taskkill /f /t /IM worker.exe'
    result = subprocess.check_output('tasklist /svc', shell=True)
    if 'worker' in result:
        result = subprocess.check_output(command, shell=True)
        _logger.debug(result)

    # 重命名旧文件
    history = []
    for f in update_list:
        if os.path.exists(f[0]) is False:
            continue
        file_name = os.path.split(f[0])[-1]
        command = 'ren {path} {name}_updated_{ts}'.format(path=f[0], name=file_name, ts=int(time.time()))
        result = subprocess.check_output(command, shell=True)
        _logger.debug(result)

    # 下载新文件
    for f in update_list:
        file_name = os.path.split(f[0])[-1]
        url = f[1]
        download_file(url=url, file_name=file_name)
        history.append([f[0], file_name])

    # 比对文件完整性

    # 重新启动
    # TODO 进程后台运行
    for f in update_list:
        suffix = os.path.splitext(f[0])[-1]
        if suffix in ('.exe',):
            command = f[0]
            subprocess.Popen(command, shell=True)

    return history


# 下载器
def handler(start=None, end=None, url=None, filename=None):
    if start and end:
        headers = {'Range': 'bytes=%d-%d' % (start, end)}
    else:
        headers = None
        start = 0
    try:
        rs = requests.get(url, headers=headers, stream=True)
    except (ConnectTimeout, ConnectionError, ReadTimeout):
        return False

    # 写入文件对应位置
    with open(filename, "r+b") as fp:
        fp.seek(start)
        fp.tell()
        fp.write(rs.content)
    return True


# 多线程下载文件入口
def download_file(url, file_name=None, num_thread=5):
    """多线程下载，默认设置线程数5，下载文件大小小于100k就单线程下载"""
    rs = requests.head(url)
    file_name = file_name if file_name else url.split('/')[-1]
    content_length = rs.headers.get('content-length', None)
    if content_length is None:
        ok = handler(url=url, filename=file_name)
        if ok:
            _logger.info(u'{filename} 更新成功'.format(filename=file_name))
            time.sleep(1)
        else:
            _logger.info(u'{filename} 更新失败, 请手动从下载并替换文件 URL: {url}'.format(filename=file_name, url=url))
            time.sleep(1)
    else:
        file_size = int(content_length)
        # 小于 100K 时单线程下载
        if file_size < 100 * 1024:
            num_thread = 1
        # Content-Length获得文件主体的大小，当http服务器使用Connection:keep-alive时，不支持Content-Length

        #  创建一个和要下载文件一样大小的文件
        fp = open(file_name, "wb")
        fp.truncate(file_size)
        fp.close()

        # 启动多线程写文件
        part = file_size // num_thread  # 如果不能整除，最后一块应该多几个字节
        _logger.info(u'{filename} 开始下载'.format(filename=file_name))
        for i in range(num_thread):
            start = part * i
            if i == num_thread - 1:  # 最后一块
                end = file_size
            else:
                end = start + part

            t = threading.Thread(target=handler, kwargs={'start': start, 'end': end, 'url': url, 'filename': file_name})
            t.setDaemon(True)
            t.start()

        # 等待所有线程下载完成
        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()
        _logger.info(u'{filename} 下载完成'.format(filename=file_name))


def main():
    # 获取当前目录下的所有文件
    file_dict = get_file_dict(APP_ROOT)

    # 获取服务器文件更新信息
    # 如果获取更新数据超时程序退出
    update_info = get_update_info(UPDATE_URL)

    # 对比文件创建时间, 生成更新文件列表
    update_list = compare_files(file_dict=file_dict, update_info=update_info)

    # 更新文件
    # 如果更新文件列表未空，程序退出
    history = updating(update_list)
    _logger.info(u"更新成功，更新历史为{history}".format(history=history if history else u'空'))
    time.sleep(1)
    return None


if __name__ == '__main__':
    main()
