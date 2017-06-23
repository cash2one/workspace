#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
import py2exe

# setup(console=["worker.py"])
options = {'py2exe': {'bundle_files': 3, 'compressed': True}}

setup(
    version="1.0.0",
    description="多线程下载",
    name="Downloader",
    options=options,
    zipfile=None,  # 不生成zip库文件
    console=["worker.py"]
)
