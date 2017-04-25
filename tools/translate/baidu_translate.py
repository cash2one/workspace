# -*- coding: utf-8 -*-
#

"""百度翻译云接口

1、将指定英文文本内容翻译为中文内容
2、将指定html格式内容翻译，返回翻译后html
"""
import re
import json
import random
import conf
import requests
from hashlib import md5
from requests import adapters


# 考虑此后可能使用多个用户，所以使用函数返回用户密钥
def get_secret():
    """
    return [appid, secretKey]
    """
    return ['20170301000040112', 'eBCB_f4abXycqX01M8u3']


class Translate(object):
    """百度云翻译接口封装翻译类"""

    def __init__(self):
        self.secret = get_secret()
        self.url_api = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
        self.data = {
            'from': 'en',
            'to': 'zh',
        }
        self.agents = conf.USER_AGENT_LIST
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        }
        request_retry = requests.adapters.HTTPAdapter(max_retries=3)
        self.session = requests.Session()
        self.session.mount("http://", request_retry)

    def text_translate(self, text):
        """
        :param text: size limit is 6000 bytes
        :return: list
        """
        # 要求q编码为utf-8
        if type(text).__name__ == 'unicode':
            text = text.encode('utf-8')
        if len(text) > 6000:
            return "Size limit is 6000 bytes"
        self.data['q'] = text
        self.data['appid'] = self.secret[0]
        self.data['salt'] = str(random.randint(23768, 65536))
        sign = self.secret[0] + text + self.data['salt'] + self.secret[1]
        m = md5()
        m.update(sign)
        self.data['sign'] = m.hexdigest()
        try:
            self.headers['User-Agent'] = random.choice(self.agents)
            response = self.session.post(self.url_api, data=self.data).text.encode("utf-8")
        except Exception as e:
            print "访问翻译接口失败"
            return e
        result = json.loads(response, encoding='UTF-8')
        # 查询空字符会返回error_code
        if result.get('error_code'):
            translated_list = []
            if result.get('error_code') == '54004':
                print "请充值！"
        else:
            translated_list = [line.get('dst').encode('utf-8').strip() for line in result.get('trans_result') if line.get('dst').strip()]
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
            clean = re.sub(r'<[^>]*>', '\n', html).splitlines()
            clean_clear = [x for x in clean if x.strip()]
            text = "\n".join(clean_clear)
            translated_list = self.text_translate(text)
            if not translated_list:
                return "翻译失败！"
            # print len(clean_clear), len(translated_list)
            for sl, tl in zip(clean_clear, translated_list):
                if isinstance(tl, str):
                    tl = unicode(tl, 'utf-8')
                html = html.replace(sl, tl.strip())
            if u'；' or '\n' in html:
                html = html.replace(u'；', ';').replace('\n', '')
            return html
        else:
            return html


if __name__ == '__main__':
    trans = Translate()
    txt = u""" """
    te = u"apple"
    p_html = """<ul>hello + </ul><p>PIC24F 16-bit Microcontroller featuring integrated Hardware Crypto module and eXtreme Low Power. This family also includes 256KB Flash, 16KB RAM, USB, LCD and advanced peripherals. The combination of features makes the part ideally suited for low power embedded security applications.</p><p>Cryptographic Engine</p><p></p><p>&nbsp;&nbsp;Performs NIST Standard Encryption/Decryption Operations without CPU Intervention</p><p>&nbsp;&nbsp;AES Cipher Support for 128, 192 and 256-Bit Keys</p><p>&nbsp;&nbsp;DES/3DES Cipher Support, with up to Three Unique Keys for 3DES</p><p>&nbsp;&nbsp;Supports ECB, CBC, OFB, CTR and CFB128 modes</p><p>&nbsp;&nbsp;Programmatically Secure OTP Array for Key Storage</p><p>&nbsp;&nbsp;True Random Number Generation</p><p>&nbsp;&nbsp;Battery-Backed RAM Key Storage</p><p> </p><p>Extreme Low-Power</p><p></p><p>&nbsp;&nbsp;Multiple Power Management Options for Extreme Power Reduction:</p><p>&nbsp;&nbsp;VBAT allows for lowest power consumption on backup battery (with or without RTCC)</p><p>&nbsp;&nbsp;Deep Sleep allows near total power-down with the ability to wake-up on external triggers</p><p>&nbsp;&nbsp;Sleep and Idle modes selectively shut down peripherals and/or core for substantial power reduction and fast wake-up</p><p>&nbsp;&nbsp;Doze mode allows CPU to run at a lower clock speed than peripherals</p><p>&nbsp;&nbsp;Alternate Clock modes allow On-the-Fly Switching to a Lower Clock Speed for Selective Power Reduction</p><p>&nbsp;&nbsp;Extreme Low-Power Current Consumption for Deep Sleep<p>&nbsp;&nbsp;WDT: 650 nA @ 2V typical</p><p>&nbsp;&nbsp;RTCC: 650 nA @ 32 kHz, 2V typical</p><p>&nbsp;&nbsp;Deep Sleep current, 60 nA typical</p></p><p>&nbsp;&nbsp;160 uA/MHz in Run mode</p><p>CPU</p><p>&nbsp;&nbsp;Modified Harvard Architecture</p><p>&nbsp;&nbsp;Up to 16 MIPS Operation @ 32 MHz</p><p>&nbsp;&nbsp;8 MHz Internal Oscillator:<p>&nbsp;&nbsp;96 MHz PLL option</p><p>&nbsp;&nbsp;Multiple clock divide options</p><p>&nbsp;&nbsp;Run-time self-calibration capability for maintaining better than ±0.20% accuracy</p><p>&nbsp;&nbsp;Fast start-up</p></p><p>&nbsp;&nbsp;17-Bit x 17-Bit Single-Cycle Hardware Fractional/Integer Multiplier</p><p>&nbsp;&nbsp;32-Bit by 16-Bit Hardware Divider</p><p>&nbsp;&nbsp;16 x 16-Bit Working Register Array</p><p>&nbsp;&nbsp;C Compiler Optimized Instruction Set Architecture</p><p>&nbsp;&nbsp;Two Address Generation Units for Separate Read and Write Addressing of Data Memory</p><p>Analog Features</p><p>&nbsp;&nbsp;10/12-Bit, up to 24-Channel Analog-to-Digital (A/D) Converter:</p><p>&nbsp;&nbsp;Conversion rate of 500 ksps (10-bit), 200 kbps (12-bit)</p><p>&nbsp;&nbsp;Auto-scan and threshold compare features</p><p>&nbsp;&nbsp;Conversion available during Sleep</p><p>&nbsp;&nbsp;One 10-Bit Digital-to-Analog Converter (DAC):</p><p>&nbsp;&nbsp;1 Msps update rate</p><p>&nbsp;&nbsp;Three Rail-to-Rail, Enhanced Analog Comparators with Programmable Input/Output Configuration</p><p>&nbsp;&nbsp;Charge Time Measurement Unit (CTMU):</p><p>&nbsp;&nbsp;Used for capacitive touch sensing, up to 24 channels</p><p>&nbsp;&nbsp;Time measurement down to 100 ps resolution</p><p>Dual Partition Flash with Live Update Capability</p><p></p><p>&nbsp;&nbsp;Capable of Holding Two Independent Software Applications, including Bootloader</p><p>&nbsp;&nbsp;Permits Simultaneous Programming of One Partition while Executing Application Code from the Other</p><p>&nbsp;&nbsp;Allows Run-Time Switching Between Active Partitions</p><p></p><p></p>"""
    # pl = [p_html, p_html, p_html]
    # print trans.text_translate(te)
    print trans.html_translate(p_html)
    # for p_html in pl:
    #     print trans.html_translate(p_html, False)
