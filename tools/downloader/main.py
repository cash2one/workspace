#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/20


# RabbitMQ
import pika
import time
import json
import config
import threading

_headers = {
    'Host': 'shopping.netsuite.com',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f'
}


# download mode

class MQProducer(threading.Thread):
    def run(self):
        while True:
            if int(time.time()) % 5 == 0:
                producer()
                time.sleep(1)


def producer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    # TODO 从指定API中获取URL，构造下载指令上传等待队列等待下载
    with open('url_list.txt', 'r') as fp:
        for line in fp.readlines():
            data = {
                'url': line.strip(),
                'headers': _headers,
                'control': {'queue': 'linear_queue'}
            }
            channel.basic_publish(exchange='',
                                  routing_key='task_queue',
                                  body=json.dumps(data),
                                  properties=pika.BasicProperties(
                                      delivery_mode=2,
                                  ))
            print(" [x] Sent {url}".format(url=line.strip()))
    connection.close()


if __name__ == '__main__':
    MQProducer().start()
