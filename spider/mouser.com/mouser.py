#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/7/6

import time
import requests
import urllib2

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Exception
from selenium.common.exceptions import NoSuchElementException, TimeoutException


Catelog_Links = []


def chrome_driver(proxy=None, headless=False, timeout=30):
    # 设置浏览器参数
    options = webdriver.ChromeOptions()
    options.binary_location = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    # 或者加入环境变量
    chrome_driver_path = r'D:\Programs\Python\Python27\selenium\webdriver\chrome\chromedriver.exe'
    if headless:
        options.add_argument('headless')
    # proxy
    if proxy is not None:
        options.add_argument('--proxy-server={proxy}'.format(proxy=proxy))
    # window size
    options.add_argument('window-size=1200x600')
    driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_driver_path)
    # 超时时间
    driver.set_page_load_timeout(timeout)
    return driver


# 检查是否出现验证码
def is_blocked(driver):
    blocked = driver.find_elements_by_class_name('dist-GlobalHeader')
    return True if blocked else False


def move_and_click(x_offset=0, y_offset=0, element=None, driver=None):
    if driver is None:
        return None
    if element is not None:
        position = element.location
        x = position.get('x', 0)
        y = position.get('y', 0)
    else:
        x, y = 0, 0
    ActionChains(driver).move_by_offset(x + x_offset, y + y_offset).click(element).perform()
    return True


def select_country(driver):
    # 如果存在选择区域，可以在空白处点击，取消选择
    try:
        select_div = driver.find_element_by_id("divContent")
        move_and_click(driver)
    except NoSuchElementException:
        pass
    except TimeoutException:
        print(u'加载时间过长，自动停止加载')
        driver.execute_script('window.stop()')


def reset_proxy(proxy, driver):
    driver.quit()
    return chrome_driver(proxy)


def load_page(url=None, driver=None, by_id=None):
    if url is None or driver is None:
        return None
    try:
        driver.get(url)
        flag = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, by_id)))
        return True
    except TimeoutException:
        flag = driver.find_elements_by_id(by_id)
        return True if flag else False


def get_proxy():
    return 'http://127.0.0.1:1080'


# 获取目录页
def get_cate_log(url, driver):
    retry = 5
    ok = False
    while retry > 0 and not ok:
        ok = load_page(url=url, driver=driver, by_id='ctl00_ctl00_ContentMain_PKCWithLeftNav_PKCLeftNav_LeftNav_lnkNewByCategory')
        if ok:
            try:
                driver.find_element_by_id("ctl00_ctl00_ContentMain_PKCWithLeftNav_PKCLeftNav_LeftNav_TV")
            except NoSuchElementException:
                continue
        else:
            if is_blocked(driver):
                proxy = get_proxy()
                driver = reset_proxy(proxy=proxy, driver=driver)
            retry -= 1
    table = driver.find_element_by_id("ctl00_ctl00_ContentMain_PKCWithLeftNav_PKCLeftNav_LeftNav_TV")
    cate_log = table.find_elements_by_tag_name('li a')
    catelog_links = [x.get_attribute('href') for x in cate_log]
    return catelog_links


def new_api(keyword):
    keyword = urllib2.quote(keyword)
    # api = "http://www.mouser.com/service/accelerationresult.aspx?keyword={search}".format(search=keyword)
    # api = 'http://www.mouser.com/_/?Keyword=LM358D&utm_source=accelerator&utm_medium=accelerator&utm_campaign=Accelerator-See-All&utm_term=LM358D'
    # api = 'http://www.mouser.com/Newest-Products/_/?Keyword=LM358D&FS=True&utm_source=accelerator&utm_medium=accelerator&utm_campaign=Accelerator-See-All&utm_term=LM358D'
    # api = 'http://www.mouser.com/search/refine.aspx?Ntk=P_MarCom&Ntt=186774745&FS=True&utm_source=accelerator&utm_medium=accelerator'
    # api = 'http://www.mouser.com/ProductDetail/STMicroelectronics/LM358D/?qs=sGAEpiMZZMtCHixnSjNA6Cq9RDS8YdICOugshCUwCZ0%3d&FS=True&utm_source=accelerator&utm_medium=accelerator'
    # api = 'http://www.mouser.com/newest/?utm_source=accelerator&utm_medium=accelerator'
    api = "http://www.mouser.com/search/refine.aspx?Ntk=P_MarCom&Ntt=156787547&utm_source=accelerator&utm_medium=accelerator"
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3141.8 Safari/537.36',
    }
    # session = requests.Session()
    rs = requests.get(url=api, headers=headers)
    # rs = session.get(url=api, headers=headers)

    print rs.text


if __name__ == '__main__':
    new_api('lm358')
    # browser = chrome_driver()
    # url = 'http://www.mouser.hk/new/'
    # print get_cate_log(url, browser)