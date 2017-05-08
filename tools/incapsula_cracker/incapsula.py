# coding=utf-8
"""
incapsula_parse(requests.session, requests.response)
    突破 incapsula 拦截，返回值类型 requests.response
sup_fetcher(fetcher)
    常用方法fetcher的装饰器，将 incap=True 开启 incapsula_parse 功能
<class> IncapSession
    继承requests.Session, 重写了get方法，返回 incapsula_parse 解析后的 requests.response
"""
import os
import re
import time
import json
import urllib
import random
import logging
import requests
import urlparse
from bs4 import BeautifulSoup
from config import USER_AGENT_LIST

# 在设置中设置默认的浏览器属性供脚本读取
setting = {
    'config': {
        'navigator': {
            'exists': True,
            'vendor': "",
            'appName': "Netscape"
        },
        'opera': {
            'exists': False
        },
        'webkitURL': {
            'exists': False,
        },
        '_phantom': {
            'exists': False
        },
        'ActiveXObject': {
            'exists': False
        }
    },
    'endpoints': {
        'cn.onlinecomponents.com': {
            'SWJIYLWA': '2977d8d74f63d7f8fedbea018b7a1d05',
            'ns': '2',
        },
        'www.ttiinc.com': {
            'SWJIYLWA': '2977d8d74f63d7f8fedbea018b7a1d05',
            'ns': '2',
        },
    }
}

# default
logger = logging.getLogger('incapsula')
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
s_handler = logging.StreamHandler()
s_handler.setFormatter(fmt)
logger.addHandler(s_handler)
endpoints = setting.get('endpoints')
config = setting.get('config')

# navigator.json 提供浏览器信息
_nav_fp = os.path.join(os.path.dirname(__file__), 'navigator.json')
with open(_nav_fp, 'r') as f:
    navigator = json.loads(f.read().decode('ascii', errors='ignore'))


# 对应 javascript test(o)
def load_config(conf=None):
    conf = config if not conf else conf
    data = []
    if conf['navigator']['exists']:
        data.append(urllib.quote('navigator=true'))
    else:
        data.append(urllib.quote('navigator=false'))
    data.append(urllib.quote('navigator.vendor=' + conf['navigator']['vendor']))
    if conf['navigator']['vendor'] is None:
        data.append(urllib.quote('navigator.vendor=nil'))
    else:
        data.append(urllib.quote('navigator.vendor=' + conf['navigator']['vendor']))
    if conf['opera']['exists']:
        data.append(urllib.quote('opera=true'))
    else:
        data.append(urllib.quote('opera=false'))
    if conf['ActiveXObject']['exists']:
        data.append(urllib.quote('ActiveXObject=true'))
    else:
        data.append(urllib.quote('ActiveXObject=false'))
    data.append(urllib.quote('navigator.appName=' + conf['navigator']['appName']))
    if conf['navigator']['appName'] is None:
        data.append(urllib.quote('navigator.appName=nil'))
    else:
        data.append(urllib.quote('navigator.appName=' + conf['navigator']['appName']))
    if conf['webkitURL']['exists']:
        data.append(urllib.quote('webkitURL=true'))
    else:
        data.append(urllib.quote('webkitURL=false'))
    if len(navigator.get('plugins', {})) == 0:
        data.append(urllib.quote('navigator.plugins.length==0=false'))
    else:
        data.append(urllib.quote('navigator.plugins.length==0=true'))
    if not navigator.get('plugins'):
        data.append(urllib.quote('navigator.plugins.length==0=nil'))
    else:
        data.append(
            urllib.quote(
                'navigator.plugins.length==0=' + 'false' if len(navigator.get('plugins', {})) == 0 else 'true'))
    if conf['_phantom']['exists']:
        data.append(urllib.quote('_phantom=true'))
    else:
        data.append(urllib.quote('_phantom=false'))
    return data


def load_plugin_extensions(plugins):
    _extensions = []
    for k, v in plugins.items():
        logger.debug('calculating plugin_extension key={}'.format(k))
        if not isinstance(v, dict):
            continue
        filename = v.get('filename')
        if not filename:
            _extensions.append(urllib.quote('plugin_ext=plugins[i] is undefined'))
            break
        if len(filename.split('.')) == 2:
            extension = filename.split('.')[-1]
            if extension not in _extensions:
                _extensions.append(extension)
    return [urllib.quote('plugin_ext={}'.format(x)) for x in _extensions]


def load_plugin(plugins):
    for k, v in plugins.items():
        logger.debug('calculating plugin key={}'.format(k))
        if '.' in v.get('filename', ''):
            filename, extension = v['filename'].split('.')
            return urllib.quote('plugin={}'.format(extension))


def _get_session_cookies(sess):
    """
    获取第一次访问时获得的cookies，交给 set_incap_cookies 生成新的cookies
    :param sess: requests.Session
    :return: dict
    """
    cookies_ = []
    for cookie_key, cookie_value in sess.cookies.items():
        if 'incap_ses_' in cookie_key:
            cookies_.append(cookie_value)
    return cookies_


def simple_digest(mystr):
    res = 0
    for c in mystr:
        res += ord(c)
    return res


def now_in_seconds():
    return time.time()


def create_cookie(name, value, seconds, url):
    """
    incapsula cookies的模板
    :param name: 
    :param value: 
    :param seconds: 
    :param url: 
    :return: 
    """
    cookie = {
        'version': '0',
        'name': name,
        'value': value,
        'port': None,
        'domain': urlparse.urlsplit(url).netloc,
        'path': '/',
        'secure': False,
        'expires': now_in_seconds() + seconds,
        'discard': True,
        'comment': None,
        'comment_url': None,
        'rest': {},
        'rfc2109': False
    }
    return cookie


def set_incap_cookie(sess, response):
    logger.debug('loading encapsula extensions and plugins')
    extensions = load_plugin_extensions(navigator['plugins'])
    extensions.append(load_plugin(navigator['plugins']))
    extensions.extend(load_config())
    cookies = _get_session_cookies(sess)
    digests = []
    for cookie in cookies:
        digests.append(simple_digest(",".join(extensions) + cookie))
    digests = [str(x) for x in digests]
    res = ",".join(extensions) + ",digest=" + ",".join(digests)
    cookie = create_cookie("___utmvc", res, 20, response.url)
    sess.cookies.set(**cookie)


def get_obfuscated_code(html):
    code = re.findall('var\s?b\s?=\s?\"(.*?)\"', html)
    return code[0]


def parse_obfuscated_code(code):
    data = []
    content = code.decode('hex')
    return content


# 正则匹配incapsula资源请求url
def get_resources(code, url):
    scheme, host = urlparse.urlsplit(url)[:2]
    resources = re.findall('(/_Incapsula_Resource.*?)\"', code)
    logger.debug('resources found: {}'.format(resources))
    return [scheme + '://' + host + r for r in resources]


def _load_encapsula_resource(sess, response):
    timing = []
    start = now_in_seconds()
    timing.append('s:{}'.format(now_in_seconds() - start))

    code = get_obfuscated_code(response.content)
    parsed = parse_obfuscated_code(code)
    # print parsed
    resources_list = list(set(get_resources(parsed, response.url)))
    for resources in resources_list:
        time.sleep(0.02)
        if '&d=' in resources:
            timing.append('c:{}'.format(now_in_seconds() - start))
            time.sleep(0.02)  # simulate page refresh time
            timing.append('r:{}'.format(now_in_seconds() - start))
            sess.get(resources + urllib.quote('complete ({})'.format(",".join(timing))))
        else:
            sess.get(resources)
            # resource1, resource2 = get_resources(parsed, response.url)[1:]
            # sess.get(resource1)
            #
            # timing.append('c:{}'.format(now_in_seconds() - start))
            # time.sleep(0.02)  # simulate page refresh time
            # timing.append('r:{}'.format(now_in_seconds() - start))
            # sess.get(resource2 + urllib.quote('complete ({})'.format(",".join(timing))))


def incapsula_parse(sess, response, **kwargs):
    soup = BeautifulSoup(response.content, 'lxml')
    meta = soup.find('meta', {'name': re.compile(r'robots', re.IGNORECASE)})
    if not meta:  # if the page is not blocked, then just return the original request.
        return response
    set_incap_cookie(sess, response)

    scheme, host = urlparse.urlsplit(response.url)[:2]
    logger.debug('scheme={0} host={1}'.format(scheme, host))
    # 可能会直接返回带有已编码的js，不需要在请求end points里的url
    if get_obfuscated_code(response.content):
        _load_encapsula_resource(sess, response)
    # Incapsula告知Request unsuccessful 或者 无法直接获取到已编码的js
    elif host in endpoints:
        params = endpoints.get(host, {'SWKMTFSR': '1', 'e': random.random()})
        url_params = urllib.urlencode(params)
        logger.debug('url_params={0}'.format(url_params))
        r = sess.get('{scheme}://{host}/_Incapsula_Resource?{url_params}'.format(scheme=scheme, host=host,
                                                                        url_params=url_params), headers={'Referer': response.url})
        _load_encapsula_resource(sess, r)
    else:
        sess.get('{scheme}://{host}/_Incapsula_Resource?SWKMTFSR=1&e={rdm}'.format(scheme=scheme, host=host,
                                                                                   rdm=random.random()),
                 headers={'Referer': response.url})
        _load_encapsula_resource(sess, response)

    if 'data' in kwargs or 'json' in kwargs:
        data = kwargs.pop('data', None)
        json = kwargs.pop('json', None)
        return sess.post(response.url, data=data, json=json, **kwargs)

    return sess.get(response.url, **kwargs)


def sup_fetcher(func):
    """
    fetcher 方法的装饰器，添加功能解析Incapsula，开启将incap设置为True
    :param func: fetcher
    :return: response
    """

    def wrapper(url, data=None, incap=False, **kwargs):
        if incap:
            sess = requests.Session()
            if kwargs.get('headers', None):
                _headers = kwargs['headers']
            else:
                _headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/57.0.2987.98 Safari/537.36',
                }
            cookies = kwargs.get('cookies')
            proxies = kwargs.get('proxies')
            timeout = kwargs.get('timeout', 30)
            params = kwargs.get('params')
            if 'method' in kwargs:
                method = kwargs['method']
            else:
                method = 'GET' if data is None else 'POST'
            try:
                response = sess.request(method, url, data=data, headers=_headers, cookies=cookies,
                                        proxies=proxies, timeout=timeout, params=params)
            except:
                return None
            return incapsula_parse(sess, response)
        else:
            return func(url, data=None, **kwargs)

    return wrapper


# @sup_fetcher
# def fetcher(url, data=None, **kwargs):
#     """获取URL数据"""
#     if kwargs.get('headers', None):
#         _headers = kwargs['headers']
#     else:
#         _headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
#                           'Chrome/57.0.2987.98 Safari/537.36',
#         }
#     cookies = kwargs.get('cookies')
#     proxies = kwargs.get('proxies')
#     timeout = kwargs.get('timeout', 30)
#     params = kwargs.get('params')
#     try:
#         if 'method' in kwargs:
#             method = kwargs['method']
#         else:
#             method = 'GET' if data is None else 'POST'
#         rs = requests.request(method, url, data=data, headers=_headers,
#                               cookies=cookies, proxies=proxies,
#                               timeout=timeout, params=params)
#     except Exception as e:
#         _logger.info('请求异常 ; %s' % e)
#         return None
#
#     if rs.status_code != 200 and kwargs.get('error_halt', 1):
#         _logger.debug('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
#         return None
#
#     _page = ''
#     if 'page' in kwargs:
#         _page = '; Page : %s' % kwargs['page']
#     if not kwargs.get('hide_print', False):
#         print 'Fetch URL ：%s %s' % (rs.url.encode('utf-8'), _page)
#
#     if 'return_response' in kwargs:
#         return rs
#     return rs.text


class IncapSession(object):
    def __init__(self):
        self.session = requests.Session()
        pass

    def get(self, url, **kwargs):
        """
        返回值为 response 对象
        """
        kwargs.setdefault('allow_redirects', True)
        if 'headers' in kwargs:
            self.session.headers.update(kwargs.pop('headers'))
        else:
            self.session.headers.update({'User-Agent': random.choice(USER_AGENT_LIST)})
        r = self.session.request('GET', url, **kwargs)
        return incapsula_parse(self.session, r, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        返回值为 response 对象
        """
        if 'headers' in kwargs:
            self.session.headers.update(kwargs.pop('headers'))
        else:
            self.session.headers.update({'User-Agent': random.choice(USER_AGENT_LIST)})
        r = self.session.request('POST', url, data=data, json=json, **kwargs)
        return incapsula_parse(self.session, r, data=data, json=json, **kwargs)


class IncapsulaMiddleware(object):
    cookie_count = 0
    logger = logging.getLogger('incapsula')

    def __init__(self, crawler):
        self.crawler = crawler
        self.priority_adjust = crawler.settings.getint('RETRY_PRIORITY_ADJUST')

    def _get_session_cookies(self, request):
        cookies_ = []
        for cookie_key, cookie_value in request.cookies.items():
            if 'incap_ses_' in cookie_key:
                cookies_.append(cookie_value)
        return cookies_

    def get_incap_cookie(self, request, response):
        extensions = load_plugin_extensions(navigator['plugins'])
        extensions.append(load_plugin(navigator['plugins']))
        extensions.extend(load_config())
        cookies = self._get_session_cookies(request)
        digests = []
        for cookie in cookies:
            digests.append(simple_digest(",".join(extensions) + cookie))
        res = ",".join(extensions) + ",digest=" + ",".join(str(digests))
        cookie = create_cookie('___utmvc', res, 20, request.url)
        return cookie

    def process_response(self, request, response, spider):
        if not request.meta.get('incap_set', False):
            soup = BeautifulSoup(response.body.decode('ascii', errors='ignore'), 'lxml')
            meta = soup.find('meta', {'name': re.compile(r'robots', re.IGNORECASE)})
            if not meta:  # if the page is not blocked, then just return the original request.
                return response
            self.crawler.stats.inc_value('incap_blocked')
            self.logger.info('cracking incapsula blocked resource <{}>'.format(request.url))

            # Set generated cookie to request more cookies from incapsula resource
            cookie = self.get_incap_cookie(request, response)
            scheme, host = urlparse.urlsplit(request.url)[:2]
            url = '{scheme}://{host}/_Incapsula_Resource?SWKMTFSR=1&e={rdm}'.format(scheme=scheme, host=host,
                                                                                    rdm=random.random())
            cpy = request.copy()
            cpy.meta['incap_set'] = True
            cpy.meta['org_response'] = response
            cpy.meta['org_request'] = request
            cpy.cookies.update(cookie)
            cpy._url = url
            cpy.priority = request.priority + self.priority_adjust
            return cpy
        elif request.meta.get('incap_set', False) and not request.meta.get('incap_request_1', False):
            timing = []
            start = now_in_seconds()
            timing.append('s:{}'.format(now_in_seconds() - start))
            code = get_obfuscated_code(request.meta.get('org_response').body.decode('ascii', errors='ignore'))
            parsed = parse_obfuscated_code(code)
            resource1, resource2 = get_resources(parsed, response.url)[1:]
            cpy = request.copy()
            cpy._url = str(resource1)
            cpy.meta['resource2'] = resource2
            cpy.meta['tstart'] = start
            cpy.meta['timing'] = timing
            cpy.meta['incap_request_1'] = True
            cpy.priority = request.priority + self.priority_adjust
            return cpy
        elif request.meta.get('incap_request_1', False) and request.meta.get('incap_completed', False):
            timing = request.meta.get('timing', [])
            resource2 = request.meta.get('resource2')
            start = request.meta.get('tstart')
            timing.append('c:{}'.format(now_in_seconds() - start))
            time.sleep(0.02)
            timing.append('r:{}'.format(now_in_seconds() - start))
            cpy = request.copy()
            cpy.meta['completed_incap'] = True
            cpy._url = str(resource2) + urllib.quote('complete ({})'.format(",".join(timing)))
            cpy.priority = request.priority + self.priority_adjust
            return cpy
        self.crawler.stats.inc_value('incap_cracked')
        cpy = request.meta.get('org_request').copy()
        cpy.cookies = request.cookies
        cpy.dont_filter = True
        cpy.priority = request.priority + self.priority_adjust
        return cpy

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)


if __name__ == "__main__":
    test_url = 'http://cn.onlinecomponents.com/productsearch/'
    default_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 '
                      'Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    # 测试 incapsula_parse
    # session = requests.Session()
    # 使用正常访问
    # before_rs = session.get(url=test_url, headers=default_headers, timeout=30)
    # with open(r'html/in_before.html', 'w') as fp:
    #     fp.write(before_rs.content)
    #
    # after_rs = incapsula_parse(session, before_rs)
    # with open(r'html/in_after.html', 'w') as fp:
    #     fp.write(after_rs.content)

    # 测试 sup_fetcher
    # before_rs = fetcher(url=test_url, headers=default_headers, timeout=30, return_response=True)
    # with open(r'html/in_before.html', 'w') as fp:
    #     fp.write(before_rs.content)

    # after_rs = fetcher(url=test_url, headers=default_headers, incap=True)
    # with open(r'html/in_after.html', 'w') as fp:
    #     fp.write(after_rs.content)

    # 测试 IncapSession
    session = IncapSession()
    IncapSession_rs = session.get(url=test_url, headers=default_headers, timeout=30)
    with open(r'html/IncapSession_rs.html', 'w') as fp:
        fp.write(IncapSession_rs.content)
    pass
