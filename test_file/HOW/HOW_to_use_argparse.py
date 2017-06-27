#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/26


import argparse


def say(word):
    print word


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息',
                        action='store_true', default=False)
    parser.add_argument('-w', '--word', dest='word', help='say a word', action='store')
    args = parser.parse_args()
    if args.word:
        say(args.word)

if __name__ == '__main__':
    main()
