#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/9

import os
import os.path
import glob


def main():
    while True:
        print "hello, python"
        break


def deep():
    files_depth3 = glob.glob('*/*/*')
    dirs_depth3 = filter(lambda f: os.path.isdir(f), files_depth3)
    print files_depth3
    print dirs_depth3


def get_file_dict(root):
    """获取所在目录的文件列表"""
    if root is None:
        return None
    file_dict = dict()

    for path, dirs, files in os.walk(root, True, None):
        depth = path.replace(root, '').split('\\')[1:]
        if len(depth) == 4:
            break
        print path
    return file_dict


if __name__ == '__main__':
    app_root = os.getcwd()
    print app_root
    get_file_dict(app_root)
    # main()
    # deep()
