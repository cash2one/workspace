# coding=utf-8

from tools import box

headers = """
Host: www.microchipdirect.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Referer: http://www.microchipdirect.com/Chart.aspx?branchId=30049&mid=10&treeid=1
Accept-Encoding: gzip, deflate, sdch
Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
"""
if __name__ == "__main__":
    print box.headers_to_dict(headers)
    pass
