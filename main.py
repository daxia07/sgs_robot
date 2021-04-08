#!/usr/bin/env python3
import sys

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, \
    NoSuchElementException, ElementClickInterceptedException,\
    StaleElementReferenceException, ElementNotInteractableException
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


def catch_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt as e:
            self = args[0]
            logger.error(e)
            self.driver.save_screenshot(f'{ROOT_DIR}/page.png')
            dom = self.driver.execute_script("return document.documentElement.outerHTML")
            with open('dom.html', 'w', encoding="utf-8") as outfile:
                outfile.write(dom)
            sys.exit(0)

    return wrapper


class GameRobot:
    def __init__(self, login_timeout=300, headless=True, account_num=1):
        # running environment
        self.headless = headless
        self.account_num = account_num
        os_type = platform()
        options = Options()
        options.add_argument(f"user-data-dir={ROOT_DIR}/.cache")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f'--profile-directory={ROOT_DIR}/.cache')
        options.add_argument('--disable-gpu')
        # options.add_argument('--enable-blink-features=ScrollTopLeftInterop')
        driver_name = 'chromedriver_windows.exe'
        if headless:
            options.add_argument('--headless')
        if os_type.startswith('Linux'):
            options.add_argument("--no-sandbox")
            driver_path = f'/usr/bin/chromedriver'
            self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
        elif os_type.startswith('Windows'):
            self.driver = webdriver.Chrome(executable_path=f'{ROOT_DIR}/drivers/{driver_name}', options=options)
        else:
            raise
        self.login_timeout = login_timeout
        self.config = dotenv_values(f"{ROOT_DIR}/.env")
        self.rtn_btn_img = Image.open(f'{ROOT_DIR}/resources/ret_btn.png')
        self.rtn_btn_hash = imagehash.average_hash(self.rtn_btn_img)
        self.rtn_btn_max_diff = 5
        self.net_warn_img = Image.open(f'{ROOT_DIR}/resources/network_issue.png')
        self.net_warn_hash = imagehash.average_hash(self.net_warn_img)
        self.net_warn_max_diff = 5
        self.loading_wait_secs = 40
        self.warning_diag_img = Image.open(f'{ROOT_DIR}/resources/warn_diag.png')
        self.warn_diag_hash = imagehash.average_hash(self.warning_diag_img)
        self.warn_diag_max_diff = 5
        self.canvas = None
        self.login()
        logger.info('SGS game robot initialised')

    def reliable_click(self, element, css_selector):
        success = False
        while not success:
            try:
                element.click()
                logger.info(f'{css_selector} Button clicked, and wait for response')
                WebDriverWait(self.driver, 10).until_not(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
                success = True
            except TimeoutException:
                logger.warning(f'Timeout for button click {css_selector}! Retrying')
                continue
            except (ElementClickInterceptedException, StaleElementReferenceException, ElementNotInteractableException):
                logger.info('Click action not valid due to element no longer exit')
                return
        logger.info('Page redirected successfully')

    @catch_exception
    def login(self):
        self.driver.get("http://web.sanguosha.com/login/index.html")
        if self.headless:
            self.driver.set_window_size(1228, 730)
        else:
            self.driver.set_window_size(1278, 860)
        try:
            self.driver.implicitly_wait(10)
            logout_btn = self.driver.find_element_by_css_selector('#logoutBtn')
            logger.info('Already login, now exiting')
            self.reliable_click(logout_btn, '#logoutBtn')
            # self.driver.execute_script("arguments[0].click();", logout_btn)
            self.driver.implicitly_wait(25)
            time.sleep(10)
        except NoSuchElementException:
            logger.info('Current page is the login page')

        account = self.config[f'ACCOUNT{self.account_num}']
        logger.info(f'Logging in account {account}')
        # Wait for element to appear
        self.driver.save_screenshot(f'{ROOT_DIR}/page.png')
        # assert logout has been successful

        check_mark = WebDriverWait(self.driver, 2000).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "input.mycheckbox")))
        # self.driver.execute_script('document.querySelector("input.mycheckbox").checked = true;', check_mark)
        if not check_mark.is_selected():
            self.reliable_click(check_mark, "input.mycheckbox")
            # self.driver.execute_script("arguments[0].click();", check_mark)
        # check_mark.click()
        username_box, pass_box = self.driver.find_elements_by_css_selector('input.dobest_input')
        username_box.send_keys(self.config[f'ACCOUNT{self.account_num}'])
        pass_box.send_keys(f'{self.config[f"PASS{self.account_num}"]}\n')
        # login
        element = WebDriverWait(self.driver, 2000).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div.new_ser1')))
        # self.reliable_click(element, "div.new_ser1")
        self.driver.execute_script("arguments[0].click();", element)
        element = self.driver.find_element_by_css_selector('a#newGoInGame')
        self.reliable_click(element, "a#newGoInGame")
        # self.driver.execute_script("arguments[0].click();", element)
        # click no response
        self.driver.save_screenshot(f'{ROOT_DIR}/page.png')
        try:
            # switch to frame
            element = WebDriverWait(self.driver, 200).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'div#gameContainer > iframe')))
            self.driver.switch_to.frame(element)
            logger.info('Switched to game frame')
            time.sleep(30)
            self.driver.save_screenshot(f'{ROOT_DIR}/page.png')
            dom = self.driver.execute_script("return document.documentElement.outerHTML")
            with open('dom.html', 'w', encoding="utf-8") as outfile:
                outfile.write(dom)
            canvas = WebDriverWait(self.driver, 200).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, f'canvas#layaCanvas')))
            self.canvas = canvas
            logger.info('Canvas captured')
        except TimeoutException as e:
            logger.error('Cannot locate the canvas after logging in')
            self.driver.save_screenshot(f'{ROOT_DIR}/page.png')
            dom = self.driver.execute_script("return document.documentElement.outerHTML")
            with open('dom.html', 'w', encoding="utf-8") as outfile:
                outfile.write(dom)
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

    @catch_exception
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
        logger.info('Detecting warning dialog')
        # image of 38 *22
        if self.headless:
            area = (1184, 0, 1222, 22)
        else:
            area = (1181, 4, 1218, 26)
        top_right_corner = image.crop(area)
        # top_right_corner.show()
        top_right_corner.save(f'{ROOT_DIR}/ret_btn_screenshot.png')
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

