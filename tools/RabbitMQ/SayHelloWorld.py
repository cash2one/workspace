#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/6

import pika
import time
import threading


class MQProducer(threading.Thread):
    def run(self):
        while True:
            if int(time.time()) % 5 == 0:
                producer()
                time.sleep(1)


class MQConsumer(threading.Thread):
    def run(self):
        consumer()


def producer():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body='Hello World!')
    print(" [x] Sent 'Hello World!'")
    connection.close()


def consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(callback,
                          queue='hello',
                          no_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def main():
    MQProducer().start()
    MQConsumer().start()


if __name__ == '__main__':
    main()
