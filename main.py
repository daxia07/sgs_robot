#!/usr/bin/env python3
import base64

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

import lxml.html as lh
import lxml.html.clean as clean
from dotenv import dotenv_values
import time
import loguru as logger

logger.add('events.log', retention='5 days', backtrace=True, diagnose=True)


options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')  # Last I checked this was necessary.


def login(browser):
    config = dotenv_values(".env")
    browser.get("http://web.sanguosha.com/login/index.html")
    check_mark = browser.find_element_by_css_selector("input.mycheckbox")
    # check_mark.location_once_scrolled_into_view
    check_mark.click()
    username_box, pass_box = browser.find_elements_by_css_selector('input.dobest_input')
    username_box.send_keys(config['ACCOUNT'])
    pass_box.send_keys(f'{config["PASS"]}\n')
    # login
    element = browser.find_element_by_css_selector('div.new_ser1')
    browser.execute_script("arguments[0].click();", element)
    # browser.find_element_by_css_selector('div.new_ser1').click()
    element = browser.find_element_by_css_selector('a#newGoInGame')
    time.sleep(1)
    # browser.find_element_by_css_selector('a#newGoInGame').click()
    browser.execute_script("arguments[0].click();", element)
    try:
        element = WebDriverWait(browser, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
        # element = browser.find_element_by_css_selector('canvas#layaCanvas')
        browser.switch_to.frame(element)
        canvas = WebDriverWait(browser, 300).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'canvas#layaCanvas')))
    except TimeoutException as e:
        print(e)
        raise
    # inspect into canvas
    time.sleep(300)
    canvas_base64 = browser.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
    # decode
    canvas_png = base64.b64decode(canvas_base64)
    # save to a file
    with open(r"canvas.png", 'wb') as f:
        f.write(canvas_png)
    pass


def detect_exit_button():
    pass


def loading_wait():
    content = browser.page_source
    cleaner = clean.Cleaner()
    content = cleaner.clean_html(content)
    doc = lh.fromstring(content)
    pass


if __name__ == '__main__':
    from platform import platform
    os_type = platform()
    driver_name = 'chromedriver_windows.exe'
    if os_type.startswith('Linux'):
        driver_name = 'chromedriver'
    browser = webdriver.Chrome(f'/drivers/{driver_name}')
    browser.set_window_position(0, 0)
    browser.set_window_size(1024, 768)
    # browser = webdriver.Chrome('chromedriver_windows.exe', chrome_options=options)
    login(browser)
