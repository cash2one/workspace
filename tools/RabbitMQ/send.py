#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/6

import sys
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue')
# channel.queue_declare(queue='hello')

# channel.basic_publish(exchange='',
#                       routing_key='hello',
#                       body='Hello World!')
# print(" [x] Sent 'Hello World!'")
message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(exchange='',
                      routing_key='task_queue',
                      body=message,
                      properties=pika.BasicProperties(
                         deliv                      ))
print(" [x] Sent %r" % message)
connection.close()
ery_mode=2,  # make message persistent
