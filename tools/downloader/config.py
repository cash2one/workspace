#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/29

import random

# 更新管理配置
UPDATE_TYPE = ['.exe', '.bat', '.config']

# 上传管理配置
UPLOAD_API = 'http://192.168.13.53:8080/downloaded/'

# 通用数据
DEFAULT_HEADERS = {
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36'
}

USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.9 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/530.9',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.6 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/530.6',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/530.5',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 '
    'Chrome/27.0.1453.93 Safari/537.36',  # Ubuntu
    'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',  # IE10
    'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0))',  # IE9
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; .NET CLR 2.0.50727; .NET CLR '
    '3.0.4506.2152; .NET CLR 3.5.30729)',  # IE8
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; InfoPath.2; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET '
    'CLR 3.5.30729)',  # IE7
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 '
    'LBBROWSER',  # 猎豹浏览器
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) '  # qq浏览器 ie 6
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) ',  # qq 浏览器 ie7
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15',  # firefox
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 Firefox/21.0',  # firefox ubuntu
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0',  # firefox mac
    'Opera/9.80 (Windows NT 6.1; WOW64; U; en) Presto/2.10.229 Version/11.62',  # Opera windows
    # 'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',  # Google蜘蛛
    # 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',  # Bing蜘蛛
    # 'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',  # Yahoo蜘蛛
]

# 供应商配置数据
UPLOAD_GUIDE_BOOK = {
    'linear': {
        'headers': {
            'Host': 'shopping.netsuite.com',
            'Referer': 'http://shopping.netsuite.com/s.nl/c.402442/sc.2/.f',
        },
        'upload_url': 'http://192.168.13.53:8080/downloaded/',
    },

}
