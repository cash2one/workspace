#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Exception
from selenium.common.exceptions import NoSuchElementException, TimeoutException

START_URL = 'http://www.elecfans.com'
TIMEOUT = 30
WithoutAD = []


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


def move_and_click(driver=None, element=None, offset=(0, 0)):
    if element is not None:
        position = element.location
        x = position.get('x', 0)
        y = position.get('y', 0)
    else:
        x, y = 0, 0
    ActionChains(driver).move_by_offset(x + offset[0], y + offset[1]).click(element).perform()


def show_the_mouse(element=None, driver=None):
    ActionChains(driver).context_click(element).perform()


def click_element(driver=None, element=None, offset=(0, 0)):
    if element:
        ele = element
    else:
        return None
    ActionChains(driver).move_to_element_with_offset(ele, offset[0], offset[1]).click().perform()


def pretend_read(driver=None):
    window_size = driver.get_window_size()
    height = window_size.get('height', 600)
    for x in range(1, 5):
        move = x * height / 3
        js = "document.documentElement.scrollTop={move_offset}".format(move_offset=move)
        driver.execute_script(js)
        time.sleep(2)


def get_proxy():
    return 'http://106.46.132.2:80'


def click_ad(proxy=None):
    browser = chrome_driver(proxy)
    browser.get(START_URL)
    # 关闭中间的广告
    try:
        big_ad = WebDriverWait(browser, 5, 0.5).until(EC.presence_of_element_located((By.ID, 'fix-tdkad')))
        js = 'var child=document.getElementById("fix-tdkad");child.parentNode.removeChild(child);document.getElementById("road-block-bg").style.display="none";'
        browser.execute_script(js)
        # close_position = (big_ad.location.get('x') + big_ad.size.get('width'),
        #                   big_ad.location.get('y'))
        # ActionChains(browser).move_by_offset(close_position[0], close_position[1]).click().perform()
        time.sleep(0.5)
    except TimeoutException:
        js = 'var child=document.getElementById("fix-tdkad");child.parentNode.removeChild(child);document.getElementById("road-block-bg").style.display="none";'
        browser.execute_script(js)
    # 获取文章标题元素
    articles = browser.find_elements_by_css_selector('*[class*="headline"]')
    articles_1 = browser.find_elements_by_css_selector('.focus-panel .tab-show .text-list>li')
    articles.extend(articles_1)

    pick_one = random.choice(articles)
    move_and_click(browser, pick_one, offset=(0, 0))
    try:
        print browser.window_handles
        print browser.current_window_handle
        if len(browser.window_handles) > 1:
            # 切换到新窗口
            browser.switch_to_window(browser.window_handles[1])
            print u"切换至文章页面"
        pretend_read(browser)
        time.sleep(1)
        # 回到页面顶部
        js = "document.documentElement.scrollTop=0"
        browser.execute_script(js)
        # 找出广告元素，移动到元素并点击
        ad = browser.find_element_by_class_name('bk_link')
        click_element(driver=browser, element=ad, offset=(0, 100))
        time.sleep(1)
    except NoSuchElementException:
        print u"当前页面无法获取广告"
        browser.delete_all_cookies()
        browser.quit()
        return False
    print browser.window_handles
    print browser.current_window_handle
    # 切换到最新的窗口
    browser.switch_to_window(browser.window_handles[-1])
    # body = browser.find_element_by_tag_name('body')
    try:
        body = WebDriverWait(browser, 10, 0.5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        pretend_read(browser)
        time.sleep(3)
    except TimeoutException:
        pass
    finally:
        browser.delete_all_cookies()
        browser.quit()


# TODO 代理失效处理
# TODO 加载超时处理
# TODO 随机停留时间
# TODO 随机点击
# TODO mongo获取代理
def main():
    proxy = get_proxy()
    while True:
        click_ad(proxy)


if __name__ == "__main__":
    main()
