import imp
import time

import sublime
import sublime_plugin
import Default.exec

from . import project_settings as ps
from . import cmake_client
from . import logging

imp.reload(ps)
imp.reload(cmake_client)
imp.reload(logging)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideRunCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):

        logger.info('build called with {} {}'.format(args, kwargs))
