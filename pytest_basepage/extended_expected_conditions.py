from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, ElementNotVisibleException,\
    NoSuchElementException


class presence_of_child_located(object):
    """ An expectation for checking that an element is present on the DOM
    of a page. This does not necessarily mean that the element is visible.
    locator - used to find the element
    returns the WebElement once it is located
    """
    def __init__(self, locator, parent):
        self.locator = locator
        self.parent = parent

    def __call__(self, ignored):
        try:
            return self.parent.find_element(*self.locator)
        except NoSuchElementException as e:
            raise e
        except WebDriverException as e:
            raise e


class presence_of_all_children_located(object):
    """ An expectation for checking that there is at least one element present
    on a web page.
    locator is used to find the element
    returns the list of WebElements once they are located
    """
    def __init__(self, locator, parent):
        self.locator = locator
        self.parent = parent

    def __call__(self, ignored):
        try:
            return self.parent.find_elements(*self.locator)
        except WebDriverException as e:
            raise e


class visibility_of_child_located(object):
    """ An expectation for checking that a child element is present on the DOM of a
    page and visible. Visibility means that the element is not only displayed
    but also has a height and width that is greater than 0.
    locator - used to find the element
    parent - parent element
    returns the WebElement once it is located and visible
    """
    def __init__(self, locator, parent):
        self.locator = locator
        self.parent = parent

    def __call__(self, ignored):
        try:
            child = self.parent.find_element(*self.locator)
            return _element_if_visible(child)
        except StaleElementReferenceException:
            return False


class visibility_of_all_children_located(object):
    """ An expectation for checking that a child element is present on the DOM of a
    page and visible. Visibility means that the element is not only displayed
    but also has a height and width that is greater than 0.
    locator - used to find the element
    parent - parent element
    returns the WebElement once it is located and visible
    """
    def __init__(self, locator, parent):
        self.locator = locator
        self.parent = parent

    def __call__(self, ignored):
        try:
            children = self.parent.find_elements(*self.locator)
            for child in children:
                if not _element_if_visible(child):
                    raise ElementNotVisibleException
            return children
        except StaleElementReferenceException:
            return False


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
