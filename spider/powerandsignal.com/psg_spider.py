# coding=utf-8
import requests

headers = {
    'Host': 'www.powerandsignal.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.98 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1',
    'Referer': 'http://www.powerandsignal.com/',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
}

url = 'http://www.powerandsignal.com/Products/AllProducts/?page=1'

# resp = requests.get(url=url, headers=headers)

# print(len(resp.text))
# print(resp.text)
# with open('all_product_pg1.html', 'w') as fp:
#     fp.write(str(resp.content))

product_url = 'http://www.powerandsignal.com/Products/Product/0003062092'

resp_product = requests.get(url=product_url, headers=headers)

with open('product_0003062092.html', 'w') as fp:
    fp.write(str(resp_product.content))