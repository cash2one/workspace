# coding=utf-8
import re
import time
import random
import urllib
import requests

default_headers = {
    'Host': 'www.ttiinc.com',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.ttiinc.com/content/ttiinc/en.html',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
}

default_chrome_str = "navigator%3Dtrue,navigator.vendor%3DGoogle%20Inc.,navigator.appName%3DNetscape,navigator.plugins.length%3D%3D0%3Dfalse,navigator.platform%3DWin32,navigator.webdriver%3Dundefined,plugin_ext%3Ddll,plugin_ext%3Dno%20extention,ActiveXObject%3Dfalse,webkitURL%3Dtrue,_phantom%3Dfalse,callPhantom%3Dfalse,chrome%3Dtrue,yandex%3Dfalse,opera%3Dfalse,opr%3Dfalse,safari%3Dfalse,awesomium%3Dfalse,puffinDevice%3Dfalse,__nightmare%3Dfalse,_Selenium_IDE_Recorder%3Dfalse,document.__webdriver_script_fn%3Dfalse,document.%24cdc_asdjflasutopfhvcZLmcfl_%3Dfalse,process.version%3Dfalse,navigator.cpuClass%3Dfalse,navigator.oscpu%3Dfalse,navigator.connection%3Dfalse,window.outerWidth%3D%3D0%3Dfalse,window.outerHeight%3D%3D0%3Dfalse,window.WebGLRenderingContext%3Dtrue,document.documentMode%3Dundefined,eval.toString().length%3D33"


def get_session_cookies(cookies=None):
    cookies = cookies if cookies else {}
    if not cookies:
        return {}
    incap_cookies = []
    pattern_cookie = re.compile(r'^\s?incap_ses_')
    for item in cookies.items():
        match = pattern_cookie.match(item[0])
        if match:
            incap_cookies.append(item[1])
    return incap_cookies


def simple_digest(text):
    res = 0
    for s in text:
        res += ord(s)
    return res


def create_cookies(name=None, value=None, seconds=None):
    expires = ''
    cookies = {}
    if seconds:
        time_stamp = int(time.time()) + seconds * 1000
        date = time.gmtime(time_stamp)
        cookies['expires'] = time.strftime('%a, %d %b %Y %H:%M:%S', date) + ' GMT'
    cookies[name] = str(value)
    cookies['path'] = '/'
    return cookies


def set_incap_cookies(browser_str, cookies):
    res = ''
    _incap_cookies = get_session_cookies(cookies)
    digest = []
    for v in _incap_cookies:
        digest.append(str(simple_digest(browser_str + v)))
    res = browser_str + ",digest=" + (','.join(digest))
    return create_cookies("___utmvc", res, 20)


def _parse_incapsula_page(response, **kwargs):
    """解析incapsula cdn验证跳转页面"""
    if 'browser_str' in kwargs:
        browser_str = kwargs['browser_str']
    else:
        browser_str = "navigator%3Dtrue,navigator.vendor%3DGoogle%20Inc.,navigator.appName%3DNetscape,navigator.plugins.length%3D%3D0%3Dfalse,navigator.platform%3DWin32,navigator.webdriver%3Dundefined,plugin_ext%3Ddll,plugin_ext%3Dno%20extention,ActiveXObject%3Dfalse,webkitURL%3Dtrue,_phantom%3Dfalse,callPhantom%3Dfalse,chrome%3Dtrue,yandex%3Dfalse,opera%3Dfalse,opr%3Dfalse,safari%3Dfalse,awesomium%3Dfalse,puffinDevice%3Dfalse,__nightmare%3Dfalse,_Selenium_IDE_Recorder%3Dfalse,document.__webdriver_script_fn%3Dfalse,document.%24cdc_asdjflasutopfhvcZLmcfl_%3Dfalse,process.version%3Dfalse,navigator.cpuClass%3Dfalse,navigator.oscpu%3Dfalse,navigator.connection%3Dfalse,window.outerWidth%3D%3D0%3Dfalse,window.outerHeight%3D%3D0%3Dfalse,window.WebGLRenderingContext%3Dtrue,document.documentMode%3Dundefined,eval.toString().length%3D33"
    temp_cookies = {}
    for item in response.cookies:
        temp_cookies[item.name] = item.value
    cookies = set_incap_cookies(browser_str, temp_cookies)
    # 解析incapsula页面
    match = re.search('var\s+b\s*=\s*"([^"]+)', response.content)
    if not match:
        return None
    _incap_page = match.group(1).decode('hex')

    # 获取incapsula_url
    match = re.search(r'src = "(/_Incapsula_Resource[^"]+)"', response.content)
    incapsula_url1 = 'https://www.ttiinc.com' + match.group(1) + str(random.random()) if match else ''

    match = re.search(r'\("GET",\s*"([^"]+)",\s*false\)', _incap_page)
    incapsula_url2 = 'https://www.ttiinc.com' + match.group(1) if match else ''

    print('解析incapsula cdn验证跳转页面中......')
    try:
        if incapsula_url1:
            requests.get(url=incapsula_url1, headers=default_headers, cookies=cookies)
        if incapsula_url2:
            requests.get(url=incapsula_url2, headers=default_headers, cookies=cookies)
    except:
        return cookies
    return cookies


if __name__ == "__main__":
    tti_homepage = 'https://www.ttiinc.com/content/ttiinc/en.html'
    tti = requests.get(url=tti_homepage, headers=default_headers)
    tti_cookies = _parse_incapsula_page(tti, browser_str=default_chrome_str)
    tti = requests.get(url=tti_homepage, headers=default_headers, cookies=tti_cookies)
    with open('tti.html', 'w') as fp:
        fp.write(tti.content)
