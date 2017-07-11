#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Exception
from selenium.common.exceptions import NoSuchElementException, TimeoutException


def chrome_driver(proxy=None):
    # 设置浏览器参数
    options = webdriver.ChromeOptions()
    options.binary_location = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    # 或者加入环境变量
    chrome_driver_path = r'D:\Programs\Python\Python27\selenium\webdriver\chrome\chromedriver.exe'
    # headless
    # options.add_argument('headless')
    # proxy
    if proxy is not None:
        options.add_argument('--proxy-server={proxy}'.format(proxy=proxy))
    # window size
    options.add_argument('window-size=1200x600')
    driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_driver_path)
    return driver


TIMEOUT = 20
Browser = chrome_driver()
Browser.set_page_load_timeout(TIMEOUT)


# 设置最长加载时间，超时停止加载
def timeout(func):
    def wrapper():
        timeout_setting = 20
        start_time = time.time()
        try:
            func()
        except TimeoutException:
            print "页面加载时间过长，已停止加载，请检查元素是否加载完成"
            Browser.execute_script('window.stop()')


# 检查是否出现验证码
def is_blocked():
    blocked = Browser.find_elements_by_id('distilCaptchaForm')
    return True if blocked else False


def move_and_click(x_offset=0, y_offset=0, element=None):
    if element is not None:
        position = element.location
        x = position.get('x', 0)
        y = position.get('y', 0)
    else:
        x, y = 0, 0
    ActionChains(Browser).move_by_offset(x + x_offset, y + y_offset).click(element).perform()


# 点击空白区域
def click_blank_area():
    move_and_click(0, 0)


# 更换ip打开新页面之后检测是否出现选择国籍选项
@timeout
def select_country():
    # 如果存在选择区域，可以在空白处点击，取消选择
    try:
        select_div = Browser.find_element_by_id("divContent")
        click_blank_area()
    except NoSuchElementException:
        pass


def get_newest_catelog():
    catelog_url = 'http://www.mouser.hk/new/'
    try:
        print(u"正在访问目录页...")
        Browser.get(catelog_url)
        table = WebDriverWait(Browser, 20).until(
            EC.presence_of_element_located((By.ID, "ctl00_ctl00_ContentMain_PKCWithLeftNav_PKCLeftNav_LeftNav_TV"))
        )
        new_products_catelog = table.find_elements_by_tag_name('li')
        print(u"获取最新产品一级目录成功！")
        return new_products_catelog
    except TimeoutException:
        table = Browser.find_elements_by_id("ctl00_ctl00_ContentMain_PKCWithLeftNav_PKCLeftNav_LeftNav_TV")
        if table:
            new_products_catelog = table[0].find_elements_by_tag_name('li')
            return new_products_catelog
        elif is_blocked():
            print u"验证码阻拦！"
            return get_newest_catelog()


def main():
    get_newest_catelog()


if __name__ == "__main__":
    main()
