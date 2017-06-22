#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/20


import time
import pika
import json
import logging
import requests
import urlparse
import threading

_logger = logging.getLogger('slave')


class MQConsumer(threading.Thread):
    def run(self):
        consumer()


def consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='task_queue', durable=True)

    channel_upload = connection.channel()

    def callback(ch, method, properties, body):
        data = json.loads(body)
        if 'queue_name' in data:
            queue_name = data.pop('queue_name')
        else:
            queue_name = 'downloaded'
        response = fetcher(**data)
        channel_upload.queue_declare(queue=queue_name)
        channel_upload.basic_publish(exchange='',
                                     routing_key=queue_name,
                                     body=response,
                                     properties=pika.BasicProperties(
                                         delivery_mode=2,
                                     ))

    channel.basic_consume(callback,
                          queue='task_queue',
                          no_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def fetcher(url, data=None, **kwargs):
    """获取URL数据"""
    if kwargs.get('headers', None):
        _headers = kwargs['headers']
    else:
        host = urlparse.urlsplit(url)[1]
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/57.0.2987.98 Safari/537.36',
            'Host': host,
        }
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 30)
    params = kwargs.get('params')
    try:
        if 'method' in kwargs:
            method = kwargs['method']
        else:
            method = 'GET' if data is None else 'POST'
        rs = requests.request(method, url, data=data, headers=_headers,
                              cookies=cookies, proxies=proxies,
                              timeout=timeout, params=params)
    except Exception as e:
        _logger.info('请求异常 ; %s' % e)
        return None

    if rs.status_code != 200 and kwargs.get('error_halt', 1):
        _logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None

    _page = ''
    if 'page' in kwargs:
        _page = '; Page : %s' % kwargs['page']
    if not kwargs.get('hide_print', False):
        print 'Fetch URL ：%s %s' % (rs.url.encode('utf-8'), _page)

    if 'return_response' in kwargs:
        return rs
    return rs.text


if __name__ == '__main__':
    MQConsumer().start()
