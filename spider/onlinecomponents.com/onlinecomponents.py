# coding=utf-8
import re
from incapsula import crack
import requests
from tools.incapsula_cracker import incapsula
from tools import util as Util
from bs4 import BeautifulSoup, SoupStrainer

_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'host': 'cn.onlinecomponents.com',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate, br',
}


def cracker():
    url = 'http://cn.onlinecomponents.com/productsearch/'
    session = incapsula.IncapSession()
    response = session.get(url=url, headers=_headers, timeout=30)

    with open(r'html/IncapSession_after.html', 'w') as fp:
        fp.write(response.content)


if __name__ == "__main__":
    cracker()
