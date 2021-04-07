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
import imagehash
from PIL import Image


class LoginError(Exception):
    pass


class NetWorkBroken(Exception):
    pass


class GameRobot:
    def __init__(self, login_timeout=300):
        # running environment
        os_type = platform()
        driver_name = 'chromedriver_windows.exe'
        if os_type.startswith('Linux'):
            driver_path = f'drivers/{driver_name}'
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')  # Last I checked this was necessary.
            self.driver = webdriver.Chrome(driver_path, chrome_options=options)
        else:
            self.driver = webdriver.Chrome(f'drivers/{driver_name}')
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1080, 768)
        self.login_timeout = login_timeout
        self.config = dotenv_values(".env")
        self.rtn_btn_img = Image.open('resources/ret_btn.png')
        self.rtn_btn_hash = imagehash.average_hash(self.rtn_btn_img)
        self.rtn_btn_max_diff = 5
        self.canvas = None
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
            canvas = WebDriverWait(self.driver, 50).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'canvas#layaCanvas')))
        except TimeoutException as e:
            logger.error('Cannot locate the canvas after logging in')
            raise e
        logger.info('Canvas detected. Waiting for the game to load')
        rem_time = self.login_timeout
        time.sleep(100)
        while rem_time > 0:
            # take screenshots and compare with existing image
            self.driver.set_window_size(900, 900)
            self.driver.set_window_size(1200, 900)
            canvas.screenshot('canvas.png')
            image = Image.open('canvas.png')
            found = self.detect_ret_btn(image)
            if found:
                logger.info('Login successful')
                self.canvas = canvas
                return
            # detect network issue
            time.sleep(5)
            rem_time -= 5
        raise LoginError('Login failed')

    def keep_alive(self):
        logger.info('Looping to keep alive')
        while True:
            self.driver.execute_script("arguments[0].click();", self.canvas)
            time.sleep(5)

    def detect_ret_btn(self, image):
        # size as 1184 * 768
        top_right_corner = image.crop((1145, 0, 1182, 22))
        current_hash = imagehash.average_hash(top_right_corner)
        if abs(self.rtn_btn_hash-current_hash) < self.rtn_btn_max_diff:
            return True
        return False

    def play(self):
        pass


if __name__ == '__main__':
    gr = GameRobot()
    gr.keep_alive()

