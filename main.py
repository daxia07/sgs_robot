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
    def __init__(self, login_timeout=300, headless=True):
        # running environment
        self.headless = headless
        os_type = platform()
        driver_name = 'chromedriver_windows.exe'
        if os_type.startswith('Linux'):
            driver_path = f'drivers/{driver_name}'
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(driver_path, options=options)
        else:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(f'drivers/{driver_name}', options=options)
            if not headless:
                self.driver = webdriver.Chrome(f'drivers/{driver_name}')
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1080, 768)
        self.login_timeout = login_timeout
        self.config = dotenv_values(".env")
        self.rtn_btn_img = Image.open('resources/ret_btn.png')
        self.rtn_btn_hash = imagehash.average_hash(self.rtn_btn_img)
        self.rtn_btn_max_diff = 5
        self.net_warn_img = Image.open('resources/network_issue.png')
        self.net_warn_hash = imagehash.average_hash(self.net_warn_img)
        self.net_warn_max_diff = 5
        self.loading_wait_secs = 100
        self.warning_diag_img = Image.open('resources/warn_diag.png')
        self.warn_diag_hash = imagehash.average_hash(self.warning_diag_img)
        self.warn_diag_max_diff = 5
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
            element = WebDriverWait(self.driver, 50).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
            logger.info('Switching to game frame')
            self.driver.switch_to.frame(element)
            canvas = WebDriverWait(self.driver, 50).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'canvas#layaCanvas')))
            self.canvas = canvas
        except TimeoutException as e:
            logger.error('Cannot locate the canvas after logging in')
            raise e
        logger.info('Canvas detected. Waiting for the game to load')
        self.canvas.screenshot('canvas.png')
        image = Image.open('canvas.png')
        connected = self.detect_network_issue(image)
        if not connected:
            # refresh and check
            self.driver.refresh()
        self.wait_for_login_loading()

    def wait_for_login_loading(self):
        logger.info('Loading in process')
        time.sleep(self.loading_wait_secs)
        rem_time = self.login_timeout
        logger.info('Checking login status')
        while rem_time > 0:
            # take screenshots and compare with existing image
            # scale to adjust the canvas style
            self.driver.set_window_size(900, 900)
            self.driver.set_window_size(1200, 900)
            self.canvas.screenshot('canvas.png')
            image = Image.open('canvas.png')
            # if warning diag found, restart the browser and login again
            self.refresh_on_warning(image)
            found = self.detect_ret_btn(image)
            if found:
                logger.info('Login successful')
                return
            time.sleep(5)
            rem_time -= 5
        raise LoginError('Login failed')

    def keep_alive(self):
        logger.info('Looping to keep alive')
        import random
        found = True
        while found:
            # create screenshot
            self.canvas.screenshot('canvas.png')
            image = Image.open('canvas.png')
            self.refresh_on_warning(image)
            found = self.detect_ret_btn(image)
            if found:
                self.driver.execute_script("arguments[0].click();", self.canvas)
            else:
                logger.error(f'Login failed during keeping alive task')
                raise LoginError('')

            secs = random.randrange(5, 100)
            time.sleep(secs)

    def detect_ret_btn(self, image):
        # size as 1184 * 768
        # in headless mode the size is 1200 * 900
        if self.headless:
            top_right_corner = image.crop((1161, 0, 1198, 22))
        else:
            top_right_corner = image.crop((1145, 0, 1182, 22))
        current_hash = imagehash.average_hash(top_right_corner)
        return abs(self.rtn_btn_hash-current_hash) < self.rtn_btn_max_diff

    def detect_network_issue(self, image):
        if self.headless:
            center_diag = image.crop((407, 337, 791, 557))
        else:
            center_diag = image.crop((391, 337, 775, 557))
        current_hash = imagehash.average_hash(center_diag)
        return abs(self.net_warn_hash-current_hash) > self.net_warn_max_diff

    def detect_warning_diag(self, image):
        if self.headless:
            center_diag = image.crop((433, 272, 816, 304))
        else:
            center_diag = image.crop((417, 272, 800, 304))
        current_hash = imagehash.average_hash(center_diag)
        return abs(self.warn_diag_hash-current_hash) < self.warn_diag_max_diff

    def refresh_on_warning(self, image):
        warning_found = self.detect_warning_diag(image)
        if warning_found:
            self.login()

    def play(self):
        pass

    def check_account_status(self):
        pass


if __name__ == '__main__':
    gr = GameRobot(headless=True)
    gr.keep_alive()

