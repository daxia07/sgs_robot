#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from dotenv import dotenv_values
import time
from definitions import logger
from platform import platform


class GameRobot:
    def __init__(self, login_timeout=300):
        # running environment
        os_type = platform()
        driver_name = 'chromedriver_windows.exe'
        if os_type.startswith('Linux'):
            driver_path = f'/drivers/{driver_name}'
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')  # Last I checked this was necessary.
            self.driver = webdriver.Chrome(driver_path, chrome_options=options)
        else:
            self.driver = webdriver.Chrome(f'/drivers/{driver_name}')
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1200, 900)
        self.login_timeout = login_timeout
        self.config = dotenv_values(".env")
        self.login()
        logger.info('SGS game robot initialised')

    def login(self):
        self.driver.get("http://web.sanguosha.com/login/index.html")
        check_mark = self.driver.find_element_by_css_selector("input.mycheckbox")
        # check_mark.location_once_scrolled_into_view
        check_mark.click()
        username_box, pass_box = self.driver.find_elements_by_css_selector('input.dobest_input')
        username_box.send_keys(self.config['ACCOUNT'])
        pass_box.send_keys(f'{self.config["PASS"]}\n')
        # login
        element = self.driver.find_element_by_css_selector('div.new_ser1')
        self.driver.execute_script("arguments[0].click();", element)
        element = self.driver.find_element_by_css_selector('a#newGoInGame')
        time.sleep(1)
        self.driver.execute_script("arguments[0].click();", element)
        try:
            # switch to frame
            element = WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
            logger.info('Switching to game frame')
            self.driver.switch_to.frame(element)
            canvas = WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'canvas#layaCanvas')))
        except TimeoutException as e:
            logger.error('Cannot locate the canvas after logging in')
            raise e
        logger.info('Canvas detected. Waiting for the game to load')

    def keep_alive(self):
        pass

    def detect_ret_btn(self):
        pass

    def play(self):
        pass










if __name__ == '__main__':
    gr = GameRobot()
    gr.keep_alive()

