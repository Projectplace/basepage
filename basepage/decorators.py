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
import warnings
import functools
from selenium.common.exceptions import StaleElementReferenceException


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used.

    :param func Function to be deprecated
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func


def handle_stale(msg='', exceptions=None):
    """
    Decorator to handle stale element reference exceptions.

    :param msg: Error message
    :param exceptions: Extra exceptions to handle
    :return: the result of the decorated function
    """
    exc = [StaleElementReferenceException]
    if exceptions is not None:
        try:
            exc.extend(iter(exceptions))
        except TypeError:  # exceptions is not iterable
            exc.append(exceptions)
    exc = tuple(exc)

    if not msg:
        msg = "Could not recover from Exception(s): {}".format(', '.join([e.__name__ for e in exc]))

    def wrapper(func):
        def exc_handler(*args, **kwargs):
            import time

            timeout = 10
            poll_freq = 0.5

            end_time = time.time() + timeout
            while time.time() <= end_time:
                try:
                    return func(*args, **kwargs)
                except exc:
                    time.sleep(poll_freq)
                    poll_freq *= 1.25
                    continue
            raise RuntimeError(msg)
        return exc_handler
    return wrapper


def wait(msg='', exceptions=None, timeout=10):
    """
    Decorator to handle generic waiting situations.

    Will handle StaleElementReferenceErrors.

    :param msg: Error message
    :param exceptions: Extra exceptions to handle
    :param timeout: time to keep trying (default: 10 seconds)
    :return: the result of the decorated function
    """
    exc = [StaleElementReferenceException]
    if exceptions is not None:
        try:
            exc.extend(iter(exceptions))
        except TypeError:  # exceptions is not iterable
            exc.append(exceptions)
    exc = tuple(exc)

    if not msg:
        msg = "Could not recover from Exception(s): {}".format(', '.join([e.__name__ for e in exc]))

    def wrapper(func):
        def wait_handler(*args, **kwargs):
            import time

            poll_freq = 0.5
            end_time = time.time() + timeout
            while time.time() <= end_time:
                try:
                    value = func(*args, **kwargs)
                    if value or timeout == 0:
                        return value
                except exc:
                    pass  # continue

                time.sleep(poll_freq)
                poll_freq *= 1.25
            raise RuntimeError(msg)
        return wait_handler
    return wrapper
