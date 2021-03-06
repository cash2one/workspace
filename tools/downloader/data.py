#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/23


TEST_DATA = [
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49932/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49926/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49915/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49916/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49911/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49933/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49959/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49960/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49931/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49913/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49923/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49927/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49910/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49918/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49928/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49922/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49909/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49919/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49912/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49917/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49929/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49987/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50194/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50114/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50163/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49615/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.44754/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50113/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49397/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49754/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.45206/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50112/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.46753/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47755/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.46729/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48854/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47403/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48477/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48424/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48503/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42878/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.44376/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42880/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43747/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33530/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47855/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48007/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43923/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43748/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47856/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47854/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48491/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50296/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33569/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.31848/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43172/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.50058/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.31572/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.40276/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47887/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.30968/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47027/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.38112/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33576/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.37011/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.47308/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49798/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.45552/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33574/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43200/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33572/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.33573/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49817/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49818/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42511/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42510/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.36501/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.38516/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.43774/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.36504/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.44567/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.44568/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49642/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.38402/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49264/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.40572/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.39730/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42496/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.48525/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42512/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.42494/.f',
    'http://shopping.netsuite.com/s.nl/c.402442/it.A/id.49240/.f', ]

if __name__ == '__main__':
    pass
