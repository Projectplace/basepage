import contextlib

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException,\
    ElementNotVisibleException, WebDriverException, MoveTargetOutOfBoundsException
from selenium.webdriver.remote.webelement import WebElement

import extended_expected_conditions as eec
from wait import ActionWait


class BasePage(object):

    def __init__(self, driver, implicit_wait=30):
        """

        :param driver:
        :param implicit_wait:
        :return:
        """
        self._driver = driver
        self._implicit_wait = implicit_wait

    def __getattr__(self, item):
        """

        :param item:
        :return:
        """
        return getattr(self.driver, item)

    @property
    def driver(self):
        return self._driver

    def click(self, locator, params=None, timeout=None):
        """
        Click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout)

    def alt_click(self, locator, params=None, timeout=None):
        """
        Alt-click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout, Keys.ALT)

    def shift_click(self, locator, params=None, timeout=None):
        """
        Shift-click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        self._click(locator, params, timeout, Keys.SHIFT)

    def multi_click(self, locator, params=None, timeout=None):
        """
        Presses left control or command button depending on OS, clicks and then releases control or command key.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element
        :return: None
        """
        multi_key = Keys.LEFT_CONTROL if 'explorer' in self.driver.name else Keys.COMMAND
        self._click(locator, params, timeout, multi_key)

    def _click(self, locator, params=None, timeout=None, key=None):
        element = locator
        if not isinstance(element, WebElement):
            element = self._get(locator, ec.element_to_be_clickable, params, timeout, "Element was never clickable!")

        if key is not None:
            ActionChains(self.driver).key_down(key).click(element).key_up(key).perform()
        else:
            element.click()

    def enter_text(self, locator, text, with_click=True, with_clear=False, with_enter=False, params=None):
        """
        Enter text into a web element.

        :param locator: locator tuple or WebElement instance
        :param text: text to input
        :param with_click: clicks the input field
        :param with_clear: clears the input field
        :param with_enter: hits enter-key after text input
        :param params: (optional) locator params
        :return: None
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params)

        if with_click:
            self.click(element)

        actions = ActionChains(self.driver)
        actions.send_keys_to_element(element, text)

        if with_clear:
            element.clear()

        if with_enter:
            actions.send_keys(Keys.ENTER)

        actions.perform()

    def drag_and_drop(self, source_element, target_element):
        """
        Drag source element and drop at target element.

        Note: Target can either be a WebElement or a list with x- and y-coordinates (integers)

        :param source_element: WebElement instance
        :param target_element: WebElement instance or list of x- and y-coordinates
        :return: None
        """
        action = ActionChains(self.driver)
        if isinstance(target_element, WebElement):
            action.drag_and_drop(source_element, target_element)
        else:
            action.click_and_hold(source_element).move_by_offset(*target_element).release()

        action.perform()

    def get_present_element(self, locator, params=None, timeout=None, visible=False):
        """
        Get element present in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param visible: (optional) if the element should also be visible (default: False)
        :return: WebElement instance
        """
        expected_condition = ec.visibility_of_element_located if visible else ec.presence_of_element_located
        return self._get(locator, expected_condition, params, timeout, error_msg="Element was never present!")

    def get_visible_element(self, locator, params=None, timeout=None):
        """
        Get element both present AND visible in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: WebElement instance
        """
        return self.get_present_element(locator, params, timeout, True)

    def get_present_elements(self, locator, params=None, timeout=None, visible=False):
        """
        Get element present in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: self._implicit_wait)
        :param visible: (optional) if the element should also be visible (default: False)
        :return: WebElement instance
        """
        expected_condition = eec.visibility_of_all_elements_located if visible else ec.presence_of_all_elements_located
        return self._get(locator, expected_condition, params, timeout, error_msg="Element was never present!")

    def get_visible_elements(self, locator, params=None, timeout=None):
        """
        Get element both present AND visible in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: WebElement instance
        """
        return self.get_present_elements(locator, params, timeout, True)

    def _get(self, locator, expected_condition, params=None, timeout=None, error_msg="", **kwargs):
        """
        Get elements based on locator with optional parameters.

        Uses selenium.webdriver.support.expected_conditions to determine the state of the element(s).

        :param locator: element identifier
        :param expected_condition: expected condition of element (ie. visible, clickable, etc)
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :param kwargs: optional arguments to expected conditions
        :return: WebElement instance, list of WebElements, or None
        """
        from selenium.webdriver.support.ui import WebDriverWait

        if not isinstance(locator, WebElement):
            error_msg += "\nLocator of type <{}> with selector <{}> with params <{params}>".format(*locator, params=params)
            locator = BasePage.get_compliant_locator(*locator, params=params)

        exp_cond = expected_condition(locator, **kwargs)
        if timeout == 0:
            try:
                return exp_cond(self.driver)
            except NoSuchElementException:
                return None

        if timeout is None:
            timeout = self._implicit_wait

        error_msg += "\nExpected condition: {}" \
                     "\nTimeout: {}".format(expected_condition, timeout)

        return WebDriverWait(self.driver, timeout).until(exp_cond, error_msg)

    def scroll_element_into_view(self, selector):
        """
        Scrolls an element into view.

        :param selector: selector of element to scroll into view
        :return: None
        """
        self.execute_sync_script("$('{}')[0].scrollIntoView( true );".format(selector))

    def open_hover(self, locator, params=None):
        """
        Open a hover or popover.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :return: element hovered
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params)
        ActionChains(self.driver).move_to_element(element).perform()
        return element

    def close_hover(self, element):
        """
        Close hover by moving to a set offset "away" from the element being hovered.

        :param element: element that triggered the hover to open
        :return: None
        """
        try:
            ActionChains(self.driver).move_to_element_with_offset(element, -100, -100).perform()
        except (StaleElementReferenceException, MoveTargetOutOfBoundsException):
            pass  # Means the hover is already closed or otherwise gone

    def perform_hover_action(self, locator, func, error_msg='', exceptions=None, params=None, **kwargs):
        """
        Hovers an element and performs whatever action is specified in the supplied function.

        NOTE: Specified function MUST return a non-false value upon success!

        :param locator: locator tuple or WebElement instance
        :param func: action to perform while hovering
        :param error_msg: error message to display if hovering failed
        :param exceptions: list of exceptions (default: StaleElementReferenceException)
        :param params: (optional) locator parameters
        :param kwargs: any key word arguments to the function
        :return: result of performed action
        """
        def _do_hover():
            try:
                with self.hover(locator, params):
                    return func(**kwargs)
            except exc:
                return False

        exc = [StaleElementReferenceException]
        if exceptions is not None:
            try:
                exc.extend(iter(exceptions))
            except TypeError:  # exceptions is not iterable
                exc.append(exceptions)
        exc = tuple(exc)

        msg = error_msg if error_msg else "Performing hover actions failed!"
        return ActionWait().until(_do_hover, msg)

    @contextlib.contextmanager
    def hover(self, locator, params=None):
        """
        Context manager for hovering.

        Opens and closes the hover.

        Usage:
            with self.hover(locator, params):
                // do something with the hover

        :param locator: locator tuple
        :param params: (optional) locator params
        :return: None
        """
        # Open hover
        element = self.open_hover(locator, params)
        try:
            yield
        finally:
            # Close hover
            self.close_hover(element)

    def wait_for_zero_queries(self, timeout=5):
        """
        Waits until there are no active or pending API requests.

        Raises TimeoutException should silence not be had.

        :param timeout: time to wait for silence (default is 5 seconds)
        :return: None
        """
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(lambda s: s.execute_script("return jQuery.active === 0"))
