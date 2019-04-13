import logging
import sys
from contextlib import contextmanager
from functools import wraps
import itertools


# *****************************************************************************
#
# *****************************************************************************
def get_logger(name):
    return logging.getLogger(name)


# *****************************************************************************
#
# *****************************************************************************
def log_method_call(logger=None):

    """This decorator logs the function being called before calling it.
    You can specify the module level logger as an argument but the method will also search for
    the default named logger if the decorator is used on an instance method of a class."""

    def wrap_method_call(func):
        fname = func.__name__

        def log_func(*args, **kwargs):

            args_string = ", ".join(map(repr, itertools.chain(args, kwargs.values())))
            logger.info("{}({})".format(fname, args_string))

            return func(*args, **kwargs)
        return log_func
    return wrap_method_call
