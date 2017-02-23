"""
Copyright (C) 2016 Planview, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, ElementNotVisibleException


class visibility_of_all_elements_located(object):
    """ An expectation for checking that an element is present on the DOM of a
    page and visible. Visibility means that the element is not only displayed
    but also has a height and width that is greater than 0.
    locator - used to find the element
    returns the WebElement once it is located and visible
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            elements = _find_elements(driver, self.locator)
            for element in elements:
                if not _element_if_visible(element):
                    raise ElementNotVisibleException
            return elements
        except StaleElementReferenceException:
            return False


class invisibility_of(object):
    """ An expectation for checking that an element is NOT present on the DOM of a
    page and/or NOT visible. Visibility means that the element is not only displayed
    but also has a height and width that is greater than 0.
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, ignored):
        try:
            return _element_if_visible(self.element, visibility=False)
        except (ElementNotVisibleException, StaleElementReferenceException):
            return True


def _element_if_visible(element, visibility=True):
    return element if element.is_displayed() == visibility else False


def _find_elements(driver, locator):
    try:
        return driver.find_elements(*locator)
    except WebDriverException as e:
        raise e
