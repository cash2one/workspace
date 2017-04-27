#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/4/27


class fish(object):
    species = 'golden fish'

    def __init__(self, name):
        size = 'big'
        price = 8
        self.name = name

    def hello_fish(self):
        print "my name's {name}".format(name=self.name)

    def set_species(self):
        self.species = "white fish"

    def get_species(self):
        print fish.species
        print self.species


class pet(fish):
    def __init__(self):
        super(pet, self).__init__()
        self.date = 'today'


if __name__ == '__main__':
    import copy
    # 1、修改类变量的值会影响已经实例化的对象吗？
    fish_a = fish('joe')
    fish_b = fish('mike')
    fish_c = copy.deepcopy(fish_a)
    print "fish_class:{cl}\nfish_a:{a}\nfish_b:{b}\nclone_a:{c}".\
        format(cl=id(fish), a=id(fish_a), b=id(fish_a), c=id(fish_c))
    print "fish_class:{cl}\nfish_a:{a}\nfish_b:{b}\nclone_a:{c}".\
        format(cl=fish.species, a=fish_a.species, b=fish_b.species, c=fish_c.species)
    fish.species = "little river fish"
    print "fish_class:{cl}\nfish_a:{a}\nfish_b:{b}\nclone_a:{c}".\
        format(cl=fish.species, a=fish_a.species, b=fish_b.species, c=fish_c.species)

    # 2、在实例对象中修改类变量
    print "="*20
    fish_a.species = "amazon fish"
    print "fish_class:{cl}\nfish_a:{a}\nfish_b:{b}\nclone_a:{c}". \
        format(cl=fish.species, a=fish_a.species, b=fish_b.species, c=fish_c.species)
    fish.species = "golden fish"
    print "fish_class:{cl}\nfish_a:{a}\nfish_b:{b}\nclone_a:{c}". \
        format(cl=fish.species, a=fish_a.species, b=fish_b.species, c=fish_c.species)

    # 3、在类中覆盖类变量
    print "+"*20
    fish_d = fish('coo')
    # print fish_d.species
    fish_d.set_species()
    fish_d.get_species()
