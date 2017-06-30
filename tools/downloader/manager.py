#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/23

import os
import copy
import json
import random
import Queue
import os.path
from threading import Thread

# flask
import flask
from flask import redirect
from flask import url_for
from flask import request
from flask import jsonify
from flask import render_template

# config
import config

# 已下载完成的内容队列
DOWNLOADED_QUEUE = Queue.Queue(20)

# 指定更新的文件类型
UPDATE_TYPE = config.UPDATE_TYPE

# 供应商下载配置
UPLOAD_GUIDE_BOOK = config.UPLOAD_GUIDE_BOOK

# 默认的下载使用的头部信息
DEFAULT_HEADERS = config.DEFAULT_HEADERS

# 默认的下载内容上传接口
UPLOAD_API = config.UPLOAD_API

# flask
app = flask.Flask(__name__)

# # # 测试数据 # # #
import data
test_list = data.TEST_DATA
# # # 测试数据 # # #


# 获取下载任务，返回json格式
@app.route('/task/')
def task_manager():
    # TODO 从接口中获取下载url
    url = random.choice(test_list)
    # TODO 识别供应商类型
    supplier = 'linear'
    supplier_download_config = UPLOAD_GUIDE_BOOK.get(supplier, None)
    if supplier_download_config is None:
        return jsonify({})

    # 构造下载参数
    _headers = copy.copy(DEFAULT_HEADERS)
    _headers.update(supplier_download_config.get('headers'))
    _headers.update({'User-Agent': random.choice(config.USER_AGENT_LIST)})
    task = {
        'download': {'url': url, 'headers': _headers},
        'control': {'upload': supplier_download_config.get('upload_url')}
    }
    return jsonify(task)


# 下载完成内容上传接口
@app.route('/downloaded/', methods=['GET', 'POST'])
def downloaded_manager():
    """使用POST提交数据，使用GET访问查看最近数据"""
    if request.method == 'POST':
        content = request.form.get('content', None)
        if content is not None and content.strip():
            downloaded = {
                "content": content,
            }
            if not DOWNLOADED_QUEUE.full():
                DOWNLOADED_QUEUE.put(downloaded)
        return 'ok'
    elif request.method == 'GET':
        try:
            content = DOWNLOADED_QUEUE.get(timeout=3)
        except Queue.Empty:
            content = 'nothing here'
        return render_template('downloaded.html', title='Downloaded Manager', content=json.dumps(content))


# 长任务异步处理
# 未使用
def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


@app.route('/update/')
def update_manager():
    """遍历更新文件夹，返回更新列表，json格式"""
    app_root = os.getcwd()
    rsc_path = os.path.join(app_root, 'static')
    update_info = get_file_dict(rsc_path)
    return jsonify(update_info)


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
        # 保存文件信息
        for f in files:
            file_name, suffix = os.path.splitext(f)
            # 仅检索制定类型文件
            if suffix not in UPDATE_TYPE:
                continue
            file_path = os.path.join(path, f)
            create_time = os.stat(file_path).st_mtime
            file_dict.update({f: {'file_size': os.path.getsize(file_path), 'create_time': int(create_time)}})
    return file_dict


# 重定向下载链接
@app.route('/update/<file_name>')
def update(file_name=None):
    if file_name:
        url = url_for('static', filename=file_name)
        return redirect(url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
