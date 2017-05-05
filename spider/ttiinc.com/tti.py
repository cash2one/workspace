#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/2

import requests
from tools.incapsula_cracker import incapsula_parse, IncapSession
import json
import re
from tools.box import headers_to_dict
_headers = headers_to_dict("""Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch, br
Accept-Language:en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
Cache-Control:no-cache
Connection:keep-alive
Cookie:incap_ses_500_731139=7+rGP1vG0Ukgo9ADqVvwBrbhB1kAAAAAVtQzQCdT9m6c+BcY9vglpw==; renderid=rend02; incap_ses_490_731139=fgMZJ2teUiwcORuFy9TMBlAgCFkAAAAAUjSMJ6QEU8t2pIc6Y+ReAA==; incap_ses_532_731139=PIIVDt11gSVgruX0eAtiB4YjCFkAAAAAIUZOznZeB3+B/99o7PT9fg==; s_sq=%5B%5BB%5D%5D; _ga=GA1.2.667915121.1489570252; _gid=GA1.2.407305118.1493712114; __utmt_75e5e075f7ab2c7c6d58c241dc444533=1; __utma=132994193.667915121.1489570252.1493712115.1493714367.22; __utmb=132994193.1.10.1493714367; __utmc=132994193; __utmz=132994193.1489570252.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); visid_incap_731139=LE3UJZ6TS2C/6+D3lL8BuMQJyVgAAAAAQkIPAAAAAACA00V7AXMcWO7ULZbwNsZbb4ooMMSSq06J; incap_ses_552_731139=+v5qKmFRHEyslEbtTxmpB7tFCFkAAAAAIq6K7KYpuRk/Nq7gniyL6A==; s_cc=true; s_fid=0D910DA93DE8FF4F-1AC34B66A1B67C54; s_nr=1493714370591-Repeat; s_lv=1493714370595; s_lv_s=Less%20than%201%20day; s_vi=[CS]v1|2C6484E8051D145C-60000151A001129E[CE]
DNT:1
Host:www.ttiinc.com
Pragma:no-cache
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36""")
def main():
    home = "https://www.ttiinc.com/content/ttiinc/en.html"
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'www.ttiinc.com',
        'Content-Type':'application/json;charset=UTF-8',
    }
    # print _headers
    # r = requests.get(url=home, headers=default_headers)
    # print r.text
    # session = requests.Session()
    # session.headers.update(default_headers)
    # print session.headers
    # r = session.request('GET', home, headers=_headers, allow_redirects=False)
    # session.cookies.update(r.cookies)
    # r = session.get(home, headers=_headers)
    # resp = incapsula_parse(session, r)
    # print session.cookies
    # print resp.text
    session = IncapSession()
    default_headers['Referer'] = 'https://www.ttiinc.com/content/ttiinc/en/apps/part-search.html?searchTerms=lm358&x=true'
    data = {"searchTerms": "lm358", "inStock": "", "rohsCompliant": "", "leadFree": "", "containsLead": ""}
    process_url = 'https://www.ttiinc.com/bin/services/processData?jsonPayloadAvailable=true&osgiService=partsearchpost'
    resp = session.post(url=process_url, data=json.dumps(data), headers=default_headers, timeout=30)
    print resp.text

if __name__ == '__main__':
    main()
