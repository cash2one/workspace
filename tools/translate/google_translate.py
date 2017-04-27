# coding=utf-8
import re
import math
import config
import random
import requests


class Translate(object):
    def __init__(self):
        # self.api = "https://translation.googleapis.com/language/translate/v2"
        self.api = "https://translate.googleapis.com/translate_a/single"
        self.params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
        }
        self.agents = config.USER_AGENT_LIST
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'Host': 'translate.google.cn',
            'Referer': 'http://translate.google.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }

    def is_it_toolarge(self, text, text_list=None):
        if len(text) >= 5000:
            parts = int(math.ceil(len(text) / 5000.0))
            step = len(text_list) / parts
            short_list = [text_list[i:i + step] for i in range(0, len(text_list), step)]
            print short_list

    def it_has_chinese(self, text):
        chinese = []
        if isinstance(text, str):
            text = unicode(text, 'utf-8')
        pattern = re.compile(ur'[\u4e00-\u9fa5]')
        if pattern.search(text):
            zh_cn = re.compile(ur'[\u4e00-\u9fa5]+')
            chinese = zh_cn.findall(text)
            no_chinese = zh_cn.sub(ur'zh_cn;', text)
            # print no_chinese, chinese
            return no_chinese, chinese
        else:
            return text, chinese

    def text_translate(self, text):
        zh_cn = re.compile(r'zh_cn;')
        if isinstance(text, str):
            text = unicode(text, 'utf-8')
        chinese_filter = self.it_has_chinese(text)
        text = chinese_filter[0]
        self.params["q"] = text
        self.headers['User-Agent'] = random.choice(self.agents)
        rsp = requests.post(self.api, data=self.params, headers=self.headers).text.encode("utf-8")
        # print rsp
        rsp_list = eval(rsp.replace(",,", ",").replace(",,", ","))
        translated = [line[0] for line in rsp_list[0]]
        translated_text = "".join(translated)
        zh_mark = zh_cn.findall(translated_text)
        # print zh_mark
        # print chinese_filter[1]
        for k, v in zip(zh_mark, chinese_filter[1]):
            translated_text = translated_text.replace(k, v.encode('utf-8'))
        translated_list = translated_text.split('\n')
        translated_list = [unicode(line, 'utf-8') for line in translated_list if isinstance(line, str)]
        return translated_list

    def html_translate(self, html):
        """
        :param html:
        :param google: True means use the google translate
        :return: html
        """
        if html.strip():
            if isinstance(html, str):
                html = unicode(html, 'utf-8')
            if len(html) >= 5000:
                return self.large_html(html)
            clean = re.sub(r'<[^>]*>', '\n', html).splitlines()
            clean_clear = [x for x in clean if x.strip()]
            text = "\n".join(clean_clear)
            translated_list = self.text_translate(text)
            # print translated_list
            for sl, tl in zip(clean_clear, translated_list):
                if isinstance(tl, str):
                    tl = unicode(tl, 'utf-8')
                html = html.replace(sl, tl.strip())
            if u'；' or '\n' in html:
                html = html.replace(u'；', ';').replace('\n', '')
            return html
        else:
            return html

    def large_html(self, html):
        if html.strip():
            if isinstance(html, str):
                html = unicode(html, 'utf-8')
            parts = int(math.ceil(len(html) / 5000.0))
            clean = re.sub(r'<[^>]*>', '\n', html).splitlines()
            clean_clear = [x for x in clean if x.strip()]
            # print clean_clear
            step = len(clean_clear) / parts
            # short_list = [clean_clear[i:i + step] for i in range(0, len(clean_clear), step)]
            # check
            short_list, s_list = [], []
            text_length = 4500
            for idx, line in enumerate(clean_clear):
                text_length -= len(line)
                if text_length > 0:
                    s_list.append(line)
                elif len(line) >= 2500:
                    short_list.append([line])
                else:
                    short_list.append(s_list)
                    text_length = 4500 - 2*len(line)
                    s_list = [line]
            else:
                short_list.append(s_list)
            large_translated_list = []
            for tx in short_list:
                text = "\n".join(tx)
                # print len(text)
                if len(text) > 5000:
                    large_translated_list.append([text])
                    continue
                large_translated_list.append(self.text_translate(text))
            # print len(large_translated_list[0])
            large_translated_list = [x for l in large_translated_list for x in l]
            for sl, tl in zip(clean_clear, large_translated_list):
                if isinstance(tl, str):
                    tl = unicode(tl, 'utf-8')
                html = html.replace(sl, tl.strip())
            if u'；' or '\n' in html:
                html = html.replace(u'；', ';').replace('\n', '')
            return html
        else:
            return html


if __name__ == "__main__":
    g = Translate()
    import urllib
    text1 = """hello"""
    # print g.text_translate(text1)[0]
    print g.html_translate(text1)
    # g.it_has_chinese(tex)
    # for i in g.text_translate(text1):
    #     text1 = text1.replace(i[0].decode("unicode-escape"), unicode(i[1], 'utf-8'))
    # print text1
    # print g.large_html(text1)
