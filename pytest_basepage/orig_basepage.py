import logging
import contextlib

from test_automation.tools import WebElement, expected_conditions as ec
from test_automation.tools import NoSuchElementException, StaleElementReferenceException, TimeoutException
from test_automation.tools import extended_expected_conditions as eec

LOGGER = logging.getLogger(__name__)


class BasePage(object):
    _url = None

    _my_overview_tab_locator = ('CSS_SELECTOR', ".pp-mainnavigation__top__logo__pp-logo")
    _plan_tab_locator = ('CSS_SELECTOR', ".tool-navigation__plan")
    _administration_tab_locator = ('CSS_SELECTOR', ".tool-navigation__settings")
    _logged_in_user_locator = ('CSS_SELECTOR', ".main-navigation__user-settings__avatar")

    _legacy_timeline_locator = ('CSS_SELECTOR', ".planning-timeline-outer-container")
    _legacy_documents_tab_locator = ('CSS_SELECTOR', "div.pp-slidetabs__tab-row a.pp-slidetabs__tab:nth-of-type(5)")
    _legacy_issues_tab_locator = ('ID', "tab_issues")
    _legacy_people_tab_locator = ('ID', "tab_org")

    _tm_frame_locator = ('CSS_SELECTOR', "iframe.time_machine_documents")
    _toggle_documents_view = ('CSS_SELECTOR', "div#d3_switcher > div")

    WAIT_FOR_WEB_ELEMENT = 30

    def __init__(self, test_driver):
        self._test_driver = test_driver
        self._switch_to = SwitchTo(test_driver.driver, self)
        self._facebook_table = None

    @property
    def test_driver(self):
        return self._test_driver

    @property
    def switch_to(self):
        return self._switch_to

    def verify_on_page(self):
        """
        Assert that the expected page has been loaded.

        Needs to be overridden in the real Page Objects.

        Called implicitly by .go_to_url()

        :return: True if page loaded successfully
        """
        pass

    def get_har(self):
        """
        Get HAR dict from the proxy

        :return: HAR dict
        """
        return self.test_driver.proxy.har

    def get_current_user(self):
        """
        Get currently logged in users name.

        :return: Currently logged in user name
        """
        return self.get_attribute(self._logged_in_user_locator, 'title')

    def go_to_url(self, as_user, url_params=None, with_auth=True, full_url=None):
        """
        Go to url specified by self._url in the real Page Objects.

        Will authorize and log in the user and redirect to the url if with_auth is True, otherwise just redirects to
        the url.

        Accepts an arbitrary number of url_params.

        :param as_user: user to authorize, log in and redirect
        :param url_params: url parameters
        :param with_auth: decides if goes to url as authorized user or not
        :param full_url: If anything is passed but None we'll bypass everything and go directly to url
        :return: None
        """
        from test_automation.tools import TimeoutException, WebDriverException
        if full_url:
            # Go to the url
            self.test_driver.go_to_url(full_url)
        else:
            from test_automation.conftest import get_config

            env = get_config().option.environment
            url = BasePage.get_formatted_url(env, self._url, url_params)
            if with_auth:
                # Get an authorized login url for the user
                url = BasePage.get_authorized_url(as_user, env, url)

            # Go to the url
            try:
                self.test_driver.go_to_url(url)
            except WebDriverException as wde:
                # If we fail due to connection refused, wait 15 seconds and try again.
                error_msg = wde.msg
                if "Connection refused" in error_msg:
                    LOGGER.warning("Connection failed with message: {}\n\nRetrying in 15 seconds...".format(error_msg))
                    from time import sleep
                    sleep(15)
                    self.test_driver.go_to_url(url)
                else:
                    raise
            else:
                # Verify that you got the expected page (overridden in the Page Object)
                try:
                    self.verify_on_page()
                except TimeoutException:
                    # Sometimes the loading of the app in test hangs, this is a less than optimal workaround.
                    LOGGER.warning("Page failed to load, trying a reload...")
                    self.reload_page()
                    self.verify_on_page()

    def get_current_url(self):
        """
        Gets current absolute URL.
        :return: URL in string format
        """
        return self.test_driver.get_current_url()

    def reload_page(self):
        """
        Reload current page.

        :return: None
        """
        self.test_driver.reload_page()

    def go_to_tab(self, tab):
        """
        Goes to desired tab via the navigation.

        :param tab: Name of the tab in English - String
        :return: Page instance
        """
        if tab.lower() == "my overview":
            from test_automation.page_objects.my_overview.my_overview_page import MyOverviewPage as Page
            self.click(self._my_overview_tab_locator)
        elif tab.lower() == "plan":
            from test_automation.page_objects.plan.plan_page import PlanPage as Page
            self.click(self._plan_tab_locator)
        elif tab.lower() == "administration":
            from test_automation.page_objects.administration.administration_page import AdministrationPage as Page
            self.click(self._administration_tab_locator)
        else:
            raise NotImplementedError
        return Page(self._test_driver)

    def go_to_legacy_tab(self, tab):
        """
        Goes to desired tab via the navigation. For Classic ONLY

        :param tab: Name of the tab in English - String
        :return: Page instance
        """
        if tab.lower() == "issues":
            from test_automation.page_objects.issues.legacy_issues_page import LegacyIssuesPage as Page
            self.click(self._legacy_issues_tab_locator)
        elif tab.lower() == "people":
            from test_automation.page_objects.members.legacy_members_page import LegacyMembersPage as Page
            self.click(self._legacy_people_tab_locator)
        else:
            raise NotImplementedError
        return Page(self._test_driver)

    def click_legacy_timeline(self):
        """
        Goes to legacy plan via the timeline.

        @return: Page instance
        """
        from test_automation.page_objects.plan.legacy_plan_page import LegacyPlanPage
        self.click(self._legacy_timeline_locator)
        return LegacyPlanPage(self.test_driver)

    def get_page_title(self):
        """
        Return the (web) page title.

        :return: page title
        """
        return self.test_driver.get_title()

    def visit_shared_link(self, as_user, share_url, with_reauth=False):
        """
        Goes to specified share_url gotten from somewhere in the service and returns appropriate page object.

        :param as_user: user to authorize, log in and redirect
        :param share_url: url parameter
        :param with_reauth: will re-authorize the user, or in the case of a new user - authorize him
        :return: Page object instance
        """
        self._url = share_url
        self.go_to_url(as_user, with_auth=with_reauth)
        if "board" in share_url:
            from test_automation.page_objects.boards.board_page import BoardPage as Page
        elif "card" in share_url:
            from test_automation.page_objects.boards.card_details_pane import CardDetailsPane as Page
        else:
            raise NotImplementedError("Option has yet to be implemented!")
        return Page(self.test_driver)

    def switch_to_documents_frame(self):
        self.switch_to.frame(self.get_element(self._tm_frame_locator), wait=True)
        try:
            self.get_element(self._toggle_documents_view, timeout=5)
        except TimeoutException:
            # If the document switcher is not visible, try a page reload.
            LOGGER.warning("The document switcher was not visible, trying a page reload.")
            self.reload_page()
        self.click(self._toggle_documents_view)

    def enter_text(self, locator, text, with_click=True, with_clear=False, with_enter=False, params=None):
        """
        Enter text into a web element.

        :param locator: locator tuple or WebElement instance
        :param text: text to input
        :param with_click: if True clicks in input field
        :param with_clear: if True clears the input field
        :param with_enter: if True hits enter-key after text input
        :param params: (optional) locator params
        :return: None
        """
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params)

        if with_click:
            self.click(element)

        self.test_driver.enter_text(element, text, with_clear, with_enter)

    def click(self, locator, params=None, with_alt=False):
        """
        Click web element.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator parameters
        :param with_alt: if True will perform an alt-click
        :return: None
        """
        LOGGER.debug("Clicking element")
        element = locator
        if not isinstance(element, WebElement):
            element = self._get(locator, ec.element_to_be_clickable, params, error_msg="Element was never clickable!")
        if with_alt:
            self.test_driver.alt_click(element)
        else:
            element.click()
        LOGGER.debug("Element clicked")

    def click_element_with_text(self, locator, text, params=None, timeout=None):
        """
        Convience method to find an element by text and click the element.

        :param locator: element identifier
        :param text: text that the element should contain
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: None
        """
        element = self.get_element_with_text(locator, text, params, timeout)
        self.click(element)

    def drag_and_drop(self, source_element, target_element, source_element_params=None, target_element_params=None):
        """
        Drag web element (source) and drop on another web element (target).

        :param source_element: WebElement instance
        :param source_element_params: (optional) locator parameters
        :param target_element: WebElement instance
        :param target_element_params: (optional) locator parameters
        :return: None
        """
        if not isinstance(source_element, WebElement):
            source_element = self.get_visible_element(source_element, source_element_params)
        if not isinstance(target_element, WebElement):
            source_element = self.get_visible_element(target_element, target_element_params)
        self.test_driver.drag_and_drop(source_element, target_element)

    def drag_and_drop_mouse(self, element, x_coord, y_coord=0, params=None):
        """
        Drag web element (source) and drop mouse to a relative coordinate (in pixels)

        :param element: WebElement instance
        :param x_coord: X coordinate relative to elements position
        :param y_coord: Y coordinate relative to elements position
        :param params: (optional) locator parameters
        :return: None
        """
        if not isinstance(element, WebElement):
            element = self.get_visible_element(element, params)
        return self.test_driver.drag_and_drop_mouse(element, x_coord, y_coord)


    def select_from_drop_down_by_value(self, locator, value, params=None):
        """
        Select option from drop down widget using value.

        :param locator: locator tuple or WebElement instance
        :param value: string
        :param params: (optional) locator parameters
        :return: None
        """
        from selenium.webdriver.support.ui import Select

        element = locator
        if not isinstance(element, WebElement):
            element = self.get_element(locator, params)

        LOGGER.debug("Selecting value <{}> from drop down".format(value))
        Select(element).select_by_value(value)
        LOGGER.info("Value <{}> from drop down selected".format(value))

    def select_from_drop_down_by_text(self, drop_down_locator, option_locator, option_text):
        """
        Select option from drop down widget using text.

        :param drop_down_locator: locator tuple (if any, params needs to be in place) or WebElement instance
        :param option_locator: locator tuple (if any, params needs to be in place)
        :param option_text: text to base option selection on
        :return: None
        """
        # Open/activate drop down
        self.click(drop_down_locator)

        # Get options
        option_elements = self.get_elements(option_locator)
        for option in option_elements:
            if self.get_text(option) == option_text:
                self.click(option)
                break

    def select_from_drop_down_by_locator(self, drop_down_locator, option_locator):
        """
        Select option from drop down widget using locator.

        :param drop_down_locator: locator tuple (if any, params needs to be in place) or WebElement instance
        :param option_locator: locator tuple (if any, params needs to be in place) or WebElement instance
        :return: None
        """
        # Open/activate drop down
        self.click(drop_down_locator)

        # Click option in drop down
        self.click(option_locator)

    def shift_select(self, first_element, last_element):
        """
        Clicks a web element and shift clicks another web element.

        :param first_element: WebElement instance
        :param last_element: WebElement instance
        :return: None
        """
        LOGGER.debug("Clicking first element in shift-select")
        self.click(first_element)
        LOGGER.debug("First element clicked, clicking last element in shift-select")
        self.test_driver.shift_click(last_element)
        LOGGER.debug("Shift-selected elements")

    def multi_select(self, elements_to_select):
        """
        Multi-select any number of elements.

        :param elements_to_select: list of WebElement instances
        :return: None
        """
        # Click the first element
        first_element = elements_to_select.pop()
        LOGGER.debug("Selecting the first element in multi-select sequence")
        self.click(first_element)
        LOGGER.debug("First element selected")

        # Click the rest
        LOGGER.debug("Multi-selecting the rest of the elements")
        for index, element in enumerate(elements_to_select, start=1):
            LOGGER.debug("Selecting element {}".format(index))
            self.test_driver.multi_click(element)
            LOGGER.debug("Element {} selected".format(index))
        LOGGER.info("{} elements multi-selected".format(len(elements_to_select) + 1))

    def get_attribute(self, locator, attribute, params=None):
        """
        Get attribute from element based on locator with optional parameters.

        Calls get_element() with expected condition: visibility of element located

        :param locator: locator tuple or WebElement instance
        :param attribute: attribute to return
        :param params: (optional) locator parameters
        :return: element attribute
        """
        LOGGER.debug("Get attribute <{}> from element".format(attribute))
        element = locator
        if not isinstance(element, WebElement):
            element = self.get_element(locator, params)
        try:
            LOGGER.debug("Get attribute <{}> from element".format(attribute))
            return element.get_attribute(attribute)
        except AttributeError:
            msg = "Element with attribute <{}> was never located!".format(attribute)
            LOGGER.exception(msg)
            raise NoSuchElementException(msg)

    def get_text(self, locator, params=None, visible=True):
        """
        Get text or value from element based on locator with optional parameters.

        :param locator: element identifier
        :param params: (optional) locator parameters
        :param visible: should element be visible before getting text (default: True)
        :return: element text, value or empty string
        """
        LOGGER.debug("Get text from element")
        element = locator

        if not isinstance(element, WebElement):
            element = self.get_visible_element(locator, params) if visible else self.get_element(locator, params)

        if element.text:
            LOGGER.debug("Text <{0.text}> was found as element.text from element".format(element))
            return element.text
        else:
            try:
                LOGGER.debug("Getting text as attribute from element")
                return element.get_attribute('value')
            except AttributeError:
                LOGGER.debug("Element had no text, returning empty string")
                return ""

    def get_element_with_text(self, locator, text, params=None, timeout=None, visible=False):
        """
        Get element that contains the text <text> either by text or by attribute value.

        :param locator: locator tuple or list of WebElements
        :param text: text that the element should contain
        :param params: (optional) locator parameters
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: WebElement instance
        """
        LOGGER.debug("Get element with text <{}> using locator <{loc[1]}> and params <{}>, timeout is <{}>".format(
            text, params, timeout, loc=locator
        ))

        elements = locator
        if not isinstance(elements, list):
            elements = self.get_elements(elements, params, timeout)
            LOGGER.debug("Elements found")

        for element in elements:
            element_text = self.get_text(element)
            if element_text is not None and text in element_text.strip():
                LOGGER.debug("Element with text <{}> found".format(text))
                return element
            else:
                attrib = element.get_attribute('value')
                if attrib is not None and text in attrib.strip():
                    LOGGER.debug("Element with text <{}> as value found".format(text))
                    return element

        if timeout == 0:
            return None  # Element with text was not present, and since timeout == 0 we don't wish to fail.

        if isinstance(locator, list):
            msg = "None of the elements had the text: {}".format(text)
        else:
            msg = "Element with type <{}>, locator <{}> and text <{text}> was never located!".format(*locator, text=text)
        raise NoSuchElementException(msg)



    def find_child_element(self, element, locator, params=None):
        """
        Finds element within this element's children by CSS selector.

        :param element: WebElement
        :param locator: locator tuple
        :param params: (optional) locator params
        :return: WebElement instance
        """
        return element.find_element(*self.get_compliant_locator(*locator, params=params))

    def find_visible_child_element(self, element, locator, params=None, timeout=None):
        """
        Get child element of parent both present AND visible in the DOM.

        If timeout is 0 (zero) return WebElement instance or None, else we wait and retry for timeout and raise
        TimeoutException should the element not be found.

        :param element: parent element of type WebElement
        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: WebElement instance
        """

        LOGGER.debug("Get visible child element with expected condition <{}>, "
                     "and timeout <{}>".format(eec.visibility_of_child_element_located, timeout))

        return self._get(locator,
                         eec.visibility_of_child_element_located,
                         params,
                         timeout,
                         "Element was never visible!",
                         parent=element)

    def find_child_elements(self, element, locator, params=None):
        """
        Finds elements within this element's children by CSS selector.

        :param element: WebElement
        :param locator: locator tuple
        :param params: (optional) locator params
        :return: list of WebElements
        """
        return element.find_elements(*self.get_compliant_locator(*locator, params=params))

    def wait_for_element_to_disappear(self, locator, params=None, timeout=None):
        """
        Waits until the element is not visible (hidden) or no longer attached to the DOM.

        Raises TimeoutException if element does not become invisible.

        :param locator: locator tuple or WebElement instance
        :param params: (optional) locator params
        :param timeout: (optional) time to wait for element (default: WAIT_FOR_WEB_ELEMENT)
        :return: None
        """
        LOGGER.debug("Waiting for element to become invisible")

        if isinstance(locator, WebElement):
            exp_cond = eec.invisibility_of
        else:
            exp_cond = ec.invisibility_of_element_located

        try:
            self._get(locator, exp_cond, params, timeout, error_msg="Element never disappeard")
        except StaleElementReferenceException:
            pass  # Element was not present, ie disappeard was satisfied
        LOGGER.debug("Element gone")




    def wait_for_non_empty_text(self, locator, params=None, timeout=5):
        """
        Wait and get elements when they're populated with any text.

        :param locator: locator tuple
        :param params: (optional) locator params
        :param timeout: (optional) maximum waiting time (in seconds) (default: 5)
        :return: list of WebElements
        """
        from test_automation.tools import PPWait

        def _do_it():
            elements = self.get_elements(locator, params)
            for element in elements:
                if not self.get_text(element):
                    return False
            return elements

        return PPWait(timeout).until(_do_it, "Element text was never populated!")

    def wait_for_attribute(self, locator, attribute, value, params=None, timeout=5):
        """
        Waits for an element attribute to get a certain value.

        Note: This function re-get's the element in a loop to avoid caching or stale element issues.

        :Example:
            Wait for the class attribute to get 'board-hidden' value

        :param locator: locator tuple
        :param attribute: element attribute
        :param value: attribute value to wait for
        :param params: (optional) locator params
        :param timeout: (optional) maximum waiting time (in seconds) (default: 5)
        :return: None
        """
        from test_automation.tools import PPWait

        def _wait(me, _locator, _attribute, _value, _params):
            element = me.get_element(_locator, _params)
            return _value in me.get_attribute(element, _attribute)

        PPWait(timeout).until(_wait, "Attribute never set!", self, locator, attribute, value, params)





    @staticmethod
    def get_compliant_locator(by, locator, params=None):
        """
        Returns a tuple of by and locator prepared with optional parameters.

        :param by: Type of locator (ie. CSS, ClassName, etc)
        :param locator: element locator
        :param params: (optional) locator parameters
        :return: tuple of by and locator with optional parameters
        """
        from selenium.webdriver.common.by import By

        if params is not None and not isinstance(params, dict):
            raise TypeError("<params> need to be of type <dict>, was <{}>".format(params.__class__.__name__))

        LOGGER.debug("Get compliant locator with by <{}>, locator <{}> and params <{}>".format(by, locator, params))
        return getattr(By, by), locator.format(**(params if params else {}))

class SwitchTo:

    _iframe_locator = ('CSS_SELECTOR', 'iframe')

    def __init__(self, driver, base_page):
        self._driver = driver
        self._base_page = base_page
        self._previous_window = None

    def previous(self):
        """
        Switches back to previous window.

        :return: None
        """
        self._driver.switch_to.window(self._previous_window)

    def frame(self, frame_reference, wait=False):
        """
        Switches focus to the specified frame, by index, name, or webelement.

        @param frame_reference: name, webelement or index
        @param wait: wait for iframe before switching to it (default: False)
        @return: None
        """
        self._previous_window = self._driver.current_window_handle
        if wait:
            self._base_page.get_element(self._iframe_locator)
        self._driver.switch_to.frame(frame_reference)
