# coding=utf-8
import requests
from conf.config import DEFAULT_HEADERS
from tools.box import add_host_into_headers


def diff_content_text():
    test_url = 'https://www.baidu.com'
    headers = add_host_into_headers(url=test_url, headers=DEFAULT_HEADERS)
    response = requests.get(url=test_url, headers=headers)
    print("response.content type: {content} \n"
          "response.text type: {text}".format(content=type(response.content), text=type(response.text)))

if __name__ == "__main__":
    diff_content_text()
    pass
