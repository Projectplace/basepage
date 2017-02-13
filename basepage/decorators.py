from selenium.common.exceptions import StaleElementReferenceException


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

            value = None
            end_time = time.time() + timeout
            while time.time() <= end_time:
                try:
                    value = func(*args, **kwargs)
                except exc:
                    pass  # continue

                time.sleep(poll_freq)
                poll_freq *= 1.25
                if value:
                    return value
            raise RuntimeError(msg)
        return wait_handler
    return wrapper
