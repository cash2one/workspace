# coding=utf-8
import re
import os
import os.path
import locale

regex_string = {
    'headers': r'([^\s:]+):\s?([^\n]*)\s*',
    'cookies': r'([^=]+)=([^;]+);?\s*',
}


def str_to_unicode(text=''):
    if text:
        if isinstance(text, str):
            return text.decode('utf-8')
        else:
            return text
    else:
        return u''


def unicode_to_str(text=''):
    if text:
        if isinstance(text, unicode):
            return text.encode('utf-8')
        else:
            return text
    else:
        return ''


def headers_to_dict(headers):
    return str_to_dict(headers, pattern=regex_string['headers'])


def cookies_to_dict(cookies):
    return str_to_dict(cookies, pattern=regex_string['cookies'])


def str_to_dict(src_str='', pattern=''):
    """
    
    :param src_str: 
    :param pattern: 
    :return: 
    """
    src_str = src_str if src_str else ''
    target_dict = {}
    if src_str:
        src_str_pattern = re.compile(pattern) if pattern else None
        try:
            src_str_list = src_str_pattern.findall(src_str) if src_str_pattern else []
        except Exception as e:
            raise e
        if src_str_list:
            for k, v in src_str_list:
                target_dict[k] = v
            return target_dict
        else:
            return {}
    else:
        return {}


def clear_text(text='', keep=True):
    """
    去除文本中的空字符（空格，制表符，换行符）
    :param text:文本或元素为文本的列表 
    :param keep: True 保留文本中的空格，将多个空字符替换成一个空格。
                 False 去除文本内所有空字符
    :return: 去除空字符后的文本或列表
    """
    pattern_blank = re.compile(r'\s+')
    text = text if text else ''
    if not text:
        return text
    if isinstance(text, list):
        text = [str_to_unicode(line) for line in text]
        if keep:
            text = [pattern_blank.sub(' ', line.strip()) for line in text]
        else:
            text = [pattern_blank.sub('', line.strip()) for line in text]
    elif isinstance(text, (str, unicode)):
        if keep:
            text = pattern_blank.sub(' ', text.strip())
        else:
            text = pattern_blank.sub('', text.strip())
    return text

def intval(text):
    return number_format(text, 0)


def floatval(text):
    return number_format(text, 4)

# def number_format(num=None, prices=0, index=0, auto=True):
#     """
#     将字符串中的数字全部提取并按照index索引和规定prices精度返回
#     :param num: 包含数字的字符串
#      :type: string
#     :param prices: 要求返回的数字精度
#      :type: int
#     :param index: 要求返回第几个数字，从第0个开始,最后一个为-1
#      :type: int
#     :param auto: 如果索引超出列表范围，返回最接近给定索引的数字,False返回第0个
#      :type: bool
#     :return: 返回数字
#      :type: int or float
#     """
#     pattern_number = re.compile(r'(-?\d+.?\d+)')
#     num = clear_text(num).replace(',', '') if num else ''
#     match_list = pattern_number.findall(num)
#     try:
#         num = float(match_list[index]) if num else 0.0
#     except Exception as e:
#         if auto:
#             num = match_list[len(match_list) - 1]
#         else:
#             num = match_list[0]
#     if prices > 0:
#         print float(num)
#         return float(locale.format("%.*f", (prices, float(num)), True))
#     else:
#         return int(num)


def number_format(num, places=5, index=0, smart=False):
    '''
    格式化数值

    @params
        num     可为任意数值，如果为 'kk12.3dsd' 则实际num将为 12.3; asas126.36.356sa => 126.36
        places  小数点后位数，默认为5，如果为0或者负数则返回整数值
        index   索引值，即匹配的第几个数值 - 1,除非你清楚匹配的索引值，否则建议默认
        smart   智能匹配，如果为True'时即当index无法匹配时，智能匹配至与index最近的一个，
                选择False当不匹配时会抛出异常；选择None则会匹配最小的情况
    @return
        格式化的float值或者int值
    '''
    _number_regex = None
    if not isinstance(num, (int, float)):
        if _number_regex is None:
            _number_regex = re.compile('(\-{0,1}\d*\.{0,1}\d+)')
        num = clear_text(num).replace(',','')
        match = _number_regex.findall(num)
        try:
            num = float(match[index]) if match else 0.0
        except Exception, e:
            if smart is None:
                num = match[0]
            elif smart:
                num = float(match[len(match) - 1])
            else:
                raise Exception(str(e))
    if places > 0:
        return float(locale.format("%.*f", (places, float(num)), True))
    else:
        return int(num)


def int_with_commas(x):
    """整型数带逗号输出比如1000则返回1,000"""
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + int_with_commas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


def rename_py(directory_path=None):
    """重命名py文件，将文件名中的空格' '换成下划线'_' """
    directory_path = directory_path if directory_path else ''
    history = []
    if isinstance(directory_path, (str, unicode)):
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            directory_path = os.path.normpath(directory_path)
            for dd, ds, fs in os.walk(directory_path):
                for f in fs:
                    if os.path.splitext(f)[1] == '.py':
                        # print os.path.join(dd, f), os.path.exists(os.path.join(dd, f))
                        f_no_space = f.replace(' ', '_')
                        src_file = os.path.join(dd, f)
                        dst_file = os.path.join(dd, f_no_space)
                        os.rename(src_file, dst_file)
                        history.append([src_file, dst_file])
                    else:
                        continue
            return history
        else:
            return history
    else:
        return history


if __name__ == "__main__":
    txt = """
    Host: www.cmzyk.com
    Connection: keep-alive
    Cache-Control: max-age=0
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36
    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
    Referer: http://www.cmzyk.com/
    Accept-Encoding: gzip, deflate, sdch
    Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
    Cookie: _cliid=Z5uEmWahptnoqTb6; _siteStatId=b4762f60-835e-471b-a21c-1f8de0aed3a9; _siteStatDay=20170409; _siteStatVisitorType=visitorType_3712084; Hm_lvt_761b4705a8e2199e09287d38531ea926=1491710762; Hm_lpvt_761b4705a8e2199e09287d38531ea926=1491722023; www.cmzyk.com__VSIGN=AKi_p8cFCgQzWHdzEMyt7_oC
    """
    txt2 = """_cliid=Z5uEmWahptnoqTb6; _siteStatId=b4762f60-835e-471b-a21c-1f8de0aed3a9; _siteStatDay=20170409; _siteStatVisitorType=visitorType_3712084; Hm_lvt_761b4705a8e2199e09287d38531ea926=1491710762; Hm_lpvt_761b4705a8e2199e09287d38531ea926=1491722023; www.cmzyk.com__VSIGN=AKi_p8cFCgQzWHdzEMyt7_oC"""
    print cookies_to_dict(txt2)
    print headers_to_dict(txt)
    # print type(txt)
    # t = unicode_to_str(txt)
    # print type(t)
    # print [].__class__
    # print isinstance([], list)
    # clean_me = """"""
    # print clear_text(clean_me, False)
    # test_num = 'kk12.63453dsd'
    # print number_format(test_num, 3, 0, True)
    # d = r"E:\workspace"
    # rename_py(d)
