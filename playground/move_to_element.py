#!/usr/bin/env python3
from selenium import webdriver

# import Action chains
from selenium.webdriver.common.action_chains import ActionChains

from definitions import ROOT_DIR
# create webdriver object
driver = webdriver.Chrome(f'{ROOT_DIR}/drivers/chromedriver_windows.exe')

# get geeksforgeeks.org
driver.get("https://www.geeksforgeeks.org/")

# get  element
element = driver.find_element_by_link_text("Courses")

# create action chain object
action = ActionChains(driver)

# perform the operation
action.move_to_element_with_offset(element, 100, 200).click().perform()

print('Done')