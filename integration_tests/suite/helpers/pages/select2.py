# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

# Based from https://gist.github.com/rafaelugolini/d2067a8c8c54026ac029

from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Select2(object):

    TIMEOUT = 4

    def __init__(self, element, root):
        self.browser = root
        self.element = self.browser.find_element_by_id(
            'select2-{0}-container'.format(element.get_attribute('id')))

    def click(self, element=None):
        if element is None:
            element = self.element
        click_element = ActionChains(self.browser).click_and_hold(element).release(element)
        click_element.perform()

    def open(self):
        if not self.is_open:
            self.click()
            WebDriverWait(self.browser, self.TIMEOUT).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.select2-dropdown')))

    def close(self):
        if self.is_open:
            self.click()

    def select(self, name):
        for item in self.items:
            if item.text == name:
                self.click(item)
                return

    @property
    def is_open(self):
        try:
            self.dropdown
        except NoSuchElementException:
            return False
        return True

    @property
    def dropdown(self):
        return self.browser.find_element_by_css_selector('span.select2-dropdown')

    def ajax_complete(self, driver):
        try:
            return 0 == driver.execute_script("return jQuery.active")
        except WebDriverException:
            pass

    @property
    def items(self):
        self.open()
        ajax_complete = getattr(self, 'ajax_complete')
        WebDriverWait(self.browser, self.TIMEOUT).until(ajax_complete, "Timeout waiting for page to load")
        return self.dropdown.find_elements_by_css_selector(
            'ul.select2-results__options li.select2-results__option')
