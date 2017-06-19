#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/6


import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue')
# channel.queue_declare(queue='hello')


# def callback(ch, method, properties, body):
#     print(" [x] Received %r" % body)
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    time.sleep(body.count(b'.'))
    print(" [x] Done")


channel.basic_consume(callback,
                      queue='task_queue',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
