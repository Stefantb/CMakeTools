import logging
import sys
from contextlib import contextmanager
from functools import wraps
import itertools


# class BashColors:
#     HEADER  = '\033[4;32m'
#     OKBLUE  = '\033[94m'
#     DEBUG   = '\033[0;49m'
#     INFO    = '\033[0;32m'
#     WARNING = '\033[0;93m'
#     ERROR   = '\033[0;31m'
#     FAIL    = '\033[0;31m'
#     ENDC    = '\033[0;m'

#     def disable(self):
#         self.HEADER = ''
#         self.OKBLUE = ''
#         self.INFO = ''
#         self.WARNING = ''
#         self.FAIL = ''
#         self.ENDC = ''


# class ColorPrinter(object):
#     def __init__(self, color):
#         self.formatter = '{color}{{text}}{endcolor}'.format(color=color, endcolor=BashColors.ENDC)

#     def color(self, text):
#         return self.formatter.format(text=text)

#     def print_out(self, text):
#         print(self.color(text=text))


# class YellowPrinter(ColorPrinter):
#     def __init__(self):
#         super(YellowPrinter, self).__init__(BashColors.WARNING)


# class CMakeIDELogger(logging.Logger):

#     def __init__(self, name):
#         # logging.Logger.__init__(name)

#         self.name = name

#         self.warncolor  = {'bashcolor': BashColors.WARNING}
#         self.infocolor  = {'bashcolor': BashColors.INFO}
#         self.debugcolor = {'bashcolor': BashColors.DEBUG}
#         self.errorcolor = {'bashcolor': BashColors.ERROR}
#         self.failcolor  = {'bashcolor': BashColors.FAIL}

#         self.basicformat = '%(asctime)s  %(levelname)s %(name)s | %(message)s'
#         self.colorformat = '%(bashcolor)s %(asctime)s %(name)-25s | %(message)s' + BashColors.ENDC

#         self.console_handler = None
#         self.file_handler = None
#         self.log_file = None
#         self.log_file_stack = []

#     def enable_console_log(self, enable_colors=None):

#         if enable_colors is None:
#             enable_colors = True

#         if self.name == 'CMakeIDE':
#             if self.console_handler is None:
#                 if enable_colors:
#                     console_formatter = logging.Formatter(self.colorformat)
#                 else:
#                     console_formatter = logging.Formatter(self.basicformat)

#                 self.console_handler = logging.StreamHandler(sys.stdout)
#                 self.console_handler.setLevel(logging.DEBUG)
#                 self.console_handler.setFormatter(console_formatter)

#                 super(CMakeIDELogger, self).addHandler(self.console_handler)
#         else:
#             self.warning('only the root logger is supposed to assign handlers!')

#     def is_logging_to_file(self):
#         return self.log_file is not None

#     def set_log_file_push(self, file_path, append=None):

#         self.log_file_stack.append(self.log_file)

#         self.info('\n\nLogging directed to:\n{}\n\n'.format(file_path))

#         self.set_log_file(filename=file_path, append=append)


#     def log_file_pop(self):

#         if self.log_file_stack:

#             prev_logfile_path = self.log_file_stack.pop()

#             current_file = self.log_file
#             self.info('\n\nLogging redirected back to:\n{}\n\n'.format(prev_logfile_path))

#             self.set_log_file(prev_logfile_path, append=True)

#             self.info('\n\nLogging back from:\n{}\n\n'.format(current_file))

#     def set_log_file(self, filename, append=None):

#         if self.name == 'CMakeIDE':

#             if self.file_handler:

#                 # self.info('\n\n-------------------- closing log file -----------------------\n\n')
#                 super(CMakeIDELogger, self).removeHandler(self.file_handler)
#                 self.file_handler = None
#                 self.info('Closing log file: {0}'.format(self.log_file))
#                 self.log_file = None

#             if filename:
#                 self.log_file = filename
#                 self.info('Opening log file: {0}'.format(self.log_file))

#                 file_formatter = logging.Formatter(self.basicformat)

#                 mode = 'a' if append else 'w'

#                 self.file_handler = logging.FileHandler(filename=self.log_file, mode=mode)
#                 self.file_handler.setLevel(logging.DEBUG)
#                 self.file_handler.setFormatter(file_formatter)

#                 super(CMakeIDELogger, self).addHandler(self.file_handler)

#                 # self.info('\n\n-------------------- joining log file -----------------------\n\n')
#         else:
#             self.warning('only the root logger is supposed to assign handlers!')

#     def warning(self, message, *args, **kwargs):
#         super(CMakeIDELogger, self).warning(message, *args, extra=self.warncolor, **kwargs)

#     def warn(self, message, *args, **kwargs):
#         self.warning(message, *args, **kwargs)

#     def info(self, message, *args, **kwargs):
#         super(CMakeIDELogger, self).info(message, *args, extra=self.infocolor, **kwargs)

#     def error(self, message, *args, **kwargs):
#         super(CMakeIDELogger, self).error(message, *args, extra=self.errorcolor, **kwargs)

#     def debug(self, message, *args, **kwargs):
#         super(CMakeIDELogger, self).debug(message, *args, extra=self.debugcolor, **kwargs)

#     def exception(self, exception, *args, **kwargs):
#         super(CMakeIDELogger, self).exception(exception, *args, **kwargs)

def get_logger(name):
    # logging.setLoggerClass(CMakeIDELogger)
    # return logging.getLogger('CMakeIDE.' + name)
    return logging.getLogger(name)

# def get_base_logger():
#     # logging.setLoggerClass(CMakeIDELogger)
#     return logging.getLogger('CMakeIDE')

# def basic_config(enable_colors=None):
#     loggr = get_base_logger()
#     loggr.enable_console_log(enable_colors=enable_colors)
#     loggr.setLevel(logging.DEBUG)


# def set_log_file_push(file_path):

#     base_logger = get_base_logger()
#     base_logger.set_log_file_push(file_path=file_path)


# def log_file_pop():
#     base_logger = get_base_logger()
#     base_logger.log_file_pop()


# @contextmanager
# def direct_log_flow(file_path, append=None):

#     base_logger = get_base_logger()
#     base_logger.set_log_file_push(file_path=file_path, append=append)

#     yield

#     base_logger.log_file_pop()


# @contextmanager
# def log_section(section_name, logger=None):

#     logger_dude = get_base_logger()
#     if logger is not None:
#         logger_dude = logger

#     logger_dude.info('----------------------------BEGIN {} ------------------------------------'.format(section_name))

#     yield

#     logger_dude.info('----------------------------END {} --------------------------------------'.format(section_name))


def log_method_call(logger=None):

    """This decorator logs the function being called before calling it.
    You can specify the module level logger as an argument but the method will also search for
    the default named logger if the decorator is used on an instance method of a class."""

    def wrap_method_call(func):
        fname = func.__name__
        def log_func(*args, **kwargs):
            # try:
            #     self = args[0].logger
            #     logger = loggr
            # except:
            #     pass

            args_string = ", ".join(map(repr, itertools.chain(args, kwargs.values())))
            logger.info("{}({})".format(fname, args_string))

            return func(*args, **kwargs)
        return log_func
    return wrap_method_call


# def echo(fn):
#     def wrapped(*v, **k):
#         name = fn.__name__
#         print("{}({})".format(name, ", ".join(map(repr, itertools.chain(v, k.values())))))
#         return fn(*v, **k)
#     return wrapped



# if __name__ == '__main__':
#     logger = CMakeIDELogger('CMakeIDE')
#     logger.enable_console_log()
#     logger.debug("testing")