#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/23

import os
import data
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

# 已下载完成的内容队列
DOWNLOADED_QUEUE = Queue.Queue(20)
# 指定给下载器的上传地址
UPLOAD_API = 'http://192.168.13.53:8080/downloaded/'
UPDATE_TYPE = ['.exe', '.bat', '.config']

app = flask.Flask(__name__)

# # # 测试数据 # # #
_headers = {
    'Host': 'shopping.netsuite.com',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f'
}

test_list = data.TEST_DATA
# # # 测试数据 # # #


@app.route('/task/')
def task_manager():
    url = random.choice(test_list)
    task = {
        'download': {'url': url, 'headers': _headers},
        'control': {'upload': UPLOAD_API}
    }
    return jsonify(task)


@app.route('/downloaded/', methods=['GET', 'POST'])
def downloaded_manager():
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
        for f in files:
            file_name, suffix = os.path.splitext(f)
            if suffix not in UPDATE_TYPE:
                continue
            file_path = os.path.join(path, f)
            create_time = os.stat(file_path).st_mtime
            file_dict.update({f: {'file_size': os.path.getsize(file_path), 'create_time': int(create_time)}})
    return file_dict


@app.route('/update/<file_name>')
def update(file_name=None):
    if file_name:
        url = url_for('static', filename=file_name)
        return redirect(url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
