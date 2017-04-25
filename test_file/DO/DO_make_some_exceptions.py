#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/4/24
import random


class spider_x(object):
    def __init__(self, live=1, total=2):
        self.x = int(random.random() * 10000)
        self.live = live
        self.total = total

    def run(self):
        live_pool = range(0, self.live)
        print self.x, self.x % self.total, live_pool
        if self.x % self.total in live_pool:
            return 200
        else:
            return 400



# 9/10
spider_one = spider_x(9, 10)
print spider_one.run()
# 1/2
spider_two = spider_x(5, 10)
print spider_two.run()
# < 1/2
spider_three = spider_x(3, 10)
print spider_three.run()
# > 1/2
spider_four = spider_x(7, 10)
print spider_four.run()

if __name__ == '__main__':
    pass
