#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from dotenv import dotenv_values
import time
from definitions import logger, ROOT_DIR
from platform import platform
import imagehash
from PIL import Image


class LoginError(Exception):
    pass


class NetWorkBroken(Exception):
    pass


class GameRobot:
    def __init__(self, login_timeout=300, headless=True, account_num=1):
        # running environment
        self.headless = headless
        self.account_num = account_num
        os_type = platform()
        driver_name = 'chromedriver_windows.exe'
        options = Options()
        options.add_argument(f"user-data-dir={ROOT_DIR}/.cache")
        options.add_argument(f'--profile-directory={ROOT_DIR}/.cache')
        if os_type.startswith('Linux'):
            # driver_name = 'chromedriver'
            driver_path = f'/usr/bin/chromedriver'
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(driver_path, options=options)
        elif os_type.startswith('Windows'):
            options = Options()
            if headless:
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
            self.driver = webdriver.Chrome(f'{ROOT_DIR}/drivers/{driver_name}', options=options)
        else:
            raise

        self.driver.set_window_position(0, 0)
        if self.headless:
            self.driver.set_window_size(1222, 730)
        else:
            self.driver.set_window_size(1238, 860)
        # self.driver.set_window_size(1080, 768)
        self.login_timeout = login_timeout
        self.config = dotenv_values(f"{ROOT_DIR}/.env")
        self.rtn_btn_img = Image.open(f'{ROOT_DIR}/resources/ret_btn.png')
        self.rtn_btn_hash = imagehash.average_hash(self.rtn_btn_img)
        self.rtn_btn_max_diff = 5
        self.net_warn_img = Image.open(f'{ROOT_DIR}/resources/network_issue.png')
        self.net_warn_hash = imagehash.average_hash(self.net_warn_img)
        self.net_warn_max_diff = 5
        self.loading_wait_secs = 100
        self.warning_diag_img = Image.open(f'{ROOT_DIR}/resources/warn_diag.png')
        self.warn_diag_hash = imagehash.average_hash(self.warning_diag_img)
        self.warn_diag_max_diff = 5
        self.canvas = None
        self.login()
        logger.info('SGS game robot initialised')

    def login(self):
        self.driver.get("http://web.sanguosha.com/login/index.html")
        account = self.config[f'ACCOUNT{self.account_num}']
        logger.info(f'Logging in account {account}')
        # Wait for element to appear
        check_mark = WebDriverWait(self.driver, 2000).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "input.mycheckbox")))
        self.driver.execute_script("arguments[0].click();", check_mark)
        # check_mark.click()
        username_box, pass_box = self.driver.find_elements_by_css_selector('input.dobest_input')
        username_box.send_keys(self.config[f'ACCOUNT{self.account_num}'])
        pass_box.send_keys(f'{self.config[f"PASS{self.account_num}"]}\n')
        # login
        element = WebDriverWait(self.driver, 2000).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div.new_ser1')))
        self.driver.execute_script("arguments[0].click();", element)
        element = self.driver.find_element_by_css_selector('a#newGoInGame')
        time.sleep(1)
        self.driver.execute_script("arguments[0].click();", element)
        try:
            # switch to frame
            element = WebDriverWait(self.driver, 2000).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
            logger.info('Switching to game frame')
            self.driver.switch_to.frame(element)
            canvas = WebDriverWait(self.driver, 4000).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, f'canvas#layaCanvas')))
            self.canvas = canvas
            logger.info('Canvas captured')
        except TimeoutException as e:
            logger.error('Cannot locate the canvas after logging in')
            raise e
        logger.info(f'Waiting for the game to load')
        self.canvas.screenshot(f'{ROOT_DIR}/canvas.png')
        image = Image.open(f'{ROOT_DIR}/canvas.png')
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
        # TODO: check queue
        while rem_time > 0:
            # take screenshots and compare with existing image
            # scale to adjust the canvas style
            # self.driver.set_window_size(900, 900)
            # time.sleep(2)
            self.canvas.screenshot(f'{ROOT_DIR}/canvas.png')
            image = Image.open(f'{ROOT_DIR}/canvas.png')
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
            self.canvas.screenshot(f'{ROOT_DIR}/canvas.png')
            image = Image.open(f'{ROOT_DIR}/canvas.png')
            self.refresh_on_warning(image)
            found = self.detect_ret_btn(image)
            if found:
                self.driver.execute_script("arguments[0].click();", self.canvas)
            else:
                logger.error(f'Login failed during keeping alive task')
                raise LoginError('')

            secs = random.randrange(250, 520)
            time.sleep(secs)

    def detect_ret_btn(self, image):
        # size as 1184 * 768
        # in headless mode the size is 1200 * 900
        top_right_corner = image.crop((1181, 0, 1219, 22))
        current_hash = imagehash.average_hash(top_right_corner)
        return abs(self.rtn_btn_hash-current_hash) < self.rtn_btn_max_diff

    def detect_network_issue(self, image):
        center_diag = image.crop((407, 337, 791, 557))
        current_hash = imagehash.average_hash(center_diag)
        return abs(self.net_warn_hash-current_hash) > self.net_warn_max_diff

    def detect_warning_diag(self, image):
        logger.info('Detecting warning dialog')
        center_diag = image.crop((420, 254, 803, 286))
        current_hash = imagehash.average_hash(center_diag)
        return abs(self.warn_diag_hash-current_hash) < self.warn_diag_max_diff

    def refresh_on_warning(self, image):
        warning_found = self.detect_warning_diag(image)
        if warning_found:
            logger.warning('Warning dialog found! Redo login')
            self.login()

    def play(self):
        pass

    def check_account_status(self):
        pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run SGS Robot program with options')
    parser.add_argument('-m', '--headless', help='Run in headless mode', action='store_true')
    parser.add_argument('-a', '--account', help='Which account to run', default=1)
    args = vars(parser.parse_args())
    gr = GameRobot(headless=args['headless'], account_num=args['account'])
    gr.keep_alive()

