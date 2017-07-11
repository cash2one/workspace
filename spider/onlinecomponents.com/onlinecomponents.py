# coding=utf-8
import re
# from incapsula import crack, IncapSession
import requests
from tools.incapsula_cracker import IncapSession
from bs4 import BeautifulSoup, SoupStrainer

_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'host': 'cn.onlinecomponents.com',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate, br',
}


def cracker():
    url = 'https://cn.onlinecomponents.com/molex-micro-product-5031493400.html?p=45572838'
    session = IncapSession()
    response = session.get(url=url, headers=_headers, timeout=30)
    print response.text
    # with open(r'html/IncapSession_after.html', 'w') as fp:
    #     fp.write(response.content)


if __name__ == "__main__":
    cracker()
