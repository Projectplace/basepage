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
import time

POLL_FREQUENCY = 0.5
DEFAULT_TIMEOUT = 10


class ActionWait(object):
    """
    Simple util that will run a function until successful or time runs out.
    """

    def __init__(self, timeout=DEFAULT_TIMEOUT, poll_frequency=POLL_FREQUENCY, debug=False):
        """
        Init timeout and poll frequency.

        Note: poll_frequency increases with 25% for each iteration.

        :param timeout: time to keep trying (default: 10 seconds)
        :param poll_frequency: how often to try (default: 0.5 seconds)
        :param debug: if True prints debug messages
        :return: None
        """
        self._timeout = timeout
        self._poll = poll_frequency
        self._debug = debug

        # avoid the divide by zero
        if self._poll == 0:
            self._poll = POLL_FREQUENCY

    def until(self, func, message='', *args, **kwargs):
        """
        Continues to execute the function until successful or time runs out.

        :param func: function to execute
        :param message: message to print if time ran out
        :param args: arguments
        :param kwargs: key word arguments
        :return: result of function or None
        """
        value = None
        end_time = time.time() + self._timeout
        while True:
            value = func(*args, **kwargs)
            if self._debug:
                print("Value from func within ActionWait: {}".format(value))
            if value:
                break

            time.sleep(self._poll)
            self._poll *= 1.25
            if time.time() > end_time:
                raise RuntimeError(message)
        return value
