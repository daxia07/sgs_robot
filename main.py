#!/usr/bin/env python3

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
    time.sleep(2)
    # browser.find_element_by_css_selector('a#newGoInGame').click()
    browser.execute_script("arguments[0].click();", element)
    try:
        element = WebDriverWait(browser, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
        # element = browser.find_element_by_css_selector('canvas#layaCanvas')
        browser.switch_to.frame(element)
        element = WebDriverWait(browser, 300).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'canvas#layaCanvas')))
    except TimeoutException as e:
        print(e)
    # inspect into canvas
    pass


# now canvas automation
def loading_wait():
    content = browser.page_source
    cleaner = clean.Cleaner()
    content = cleaner.clean_html(content)
    doc = lh.fromstring(content)
    pass


if __name__ == '__main__':
    browser = webdriver.Chrome('chromedriver.exe')
    # browser = webdriver.Chrome('chromedriver.exe', chrome_options=options)
    login(browser)
