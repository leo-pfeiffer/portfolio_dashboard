import logging
from functools import partial, wraps
import traceback


class FuncError(Exception):
    pass


def log(func=None, break_on_error=True, custom_name=None):

    logger = logging.getLogger('db')

    if func is None:
        return partial(log, break_on_error=break_on_error, custom_name=custom_name)

    @wraps(func)
    def auto_logger(*args, **kwargs):

        try:
            return func(*args, **kwargs)

        except BaseException as be:
            if custom_name is None:
                logger.exception('Function: {} //////  BaseException: {} //////  Traceback: {}'.format(func.__name__, be, traceback.format_exc()))
            else:
                logger.exception('{} //////  BaseException: {} //////  Traceback: {}'.format(custom_name, be, traceback.format_exc()))
            if break_on_error:
                raise be

    return auto_logger