#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/27

import os
import os.path
import requests


# 获取当前目录下的所有文件
def get_file_list(root):
    file_list = []
    dir_list = []
    for path, dirs, files in os.walk(root, True, None):
        for f in files:
            file_path = os.path.join(path, f)
            file_list.append(file_path)
        for d in dirs:
            dir_path = os.path.join(path, d)
            dir_list.append(dir_path)
    return dir_list, file_list


APP_ROOT = os.getcwd()
DIR_LIST, FILE_LIST = get_file_list(APP_ROOT)


# 对比文件列表
UPDATE = 'http://192.168.13.53:8080/update'

# 对比文件创建时间以及md5值
# 关闭已开始的进程
# 替换新文件
# 重新开启程序

def main():
    pass


if __name__ == '__main__':
    main()
