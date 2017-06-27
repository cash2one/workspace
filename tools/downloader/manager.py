#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/23

import data
import json
import random
import Queue

import flask
from flask import request
from flask import render_template

DOWNLOADED_QUEUE = Queue.Queue(20)

app = flask.Flask(__name__)

_headers = {
    'Host': 'shopping.netsuite.com',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f'
}

test_list = data.TEST_DATA
UPLOAD_API = 'http://192.168.13.53:8080/downloaded'


@app.route('/task')
def task_manager():
    url = random.choice(test_list)
    task = {
        'download': {'url': url, 'headers': _headers},
        'control': {'upload': UPLOAD_API}
    }
    return json.dumps(task)


@app.route('/downloaded', methods=['GET', 'POST'])
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


def update_manager():
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
