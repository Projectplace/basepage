Basepage
========

Basepage is a python package that enables you to write selenium tests using python easily and fast.

It provides two parts:

* A wrapper around [webdriver (selenium)](https://github.com/SeleniumHQ/selenium) and its functions and properties
* Convenience methods for dealing with elements

We recommend you use it in conjunction with the [page-object model](https://github.com/SeleniumHQ/selenium/wiki/PageObjects) (examples are in java, but the pattern works for python as well).

## Instantiation

There are a couple of ways you can use Basepage.

### Inheritance
```python
from basepage import Basepage

class MyBasepage(Basepage):
    def __init__(self, driver):
        super(BasePage, self).__init__(driver)
```
This way, Basepage becomes part of `self`, and in your page-objects you can use it like so:
```python
from mybase import MyBasepage

class Loginpage(MyBasepage):

    _username_locator = ('ID', 'username')
    _password_locator = ('ID', 'password')
    _login_button_locator = ('CSS_SELECTOR', '.login_button')

    def login(username, password):
        self.enter_text(self._username_locator, username)
        self.enter_text(self._password_locator, password)
        self.click(self._login_button_locator)
```


### Property
```python
class MyBasepage(object):
    def __init__(self, driver):
        from basepage import Basepage
        self._base = Basepage(driver)
	
    @property
    def base(self):
        return self._base
```
This way, Basepage is a property on MyBasepage, and in your page-objects you can use it like so:
```python
from mybase import MyBasepage

class Loginpage(MyBasepage):

    _username_locator = ('ID', 'username')
    _password_locator = ('ID', 'password')
    _login_button_locator = ('CSS_SELECTOR', '.login_button')

    def login(username, password):
        self.base.enter_text(self._username_locator, username)
        self.base.enter_text(self._password_locator, password)
        self.base.click(self._login_button_locator)
```

## Requirements
To be able to use Basepage you need to provide an adapter for selectors, you have to name it `get_compliant_locator`and it has to return a tuple containing a selenium [By](https://github.com/SeleniumHQ/selenium/blob/master/py/selenium/webdriver/common/by.py) selector and a string. The rest of the implementation details is up to you.

Example:
```python
from basepage import Basepage

class MyBasepage(Basepage):
    def __init__(self, driver):
        super(BasePage, self).__init__(driver)
    
    @staticmethod
    def get_compliant_locator(by, locator, params=None):
        """
        Returns a tuple of by and locator prepared with optional parameters
        :param by: Type of locator (ie. CSS, ClassName, etc)
        :param locator: element locator
        :param params: (optional) locator parameters
        :return: tuple of by and locator with optional parameters
        """
        from selenium.webdriver.common.by import By

        if params is not None and not isinstance(params, dict):
            raise TypeError("<params> need to be of type <dict>, was <{}>".format(params.__class__.__name__))

        return getattr(By, by), locator.format(**(params or {}))
```


## pytest

We recommend using the [pytest](https://github.com/pytest-dev/pytest) test framework with the [pytest-selenium](https://github.com/pytest-dev/pytest-selenium) plugin to even further cut down on implementation time.

### Example usage
Given you're using pytest and pytest-selenium, this is what a test could look like:
```python
import pytest
from login_page import Loginpage

def test_login(driver):
    page = Loginpage(driver)
    page.login("Tom Smith", "123456")
    assert something
```
The `driver` parameter is actually a fixture provided by the pytest-selenium to the pytest framework and represents an instance of webdriver.
