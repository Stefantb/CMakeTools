import imp
import time

import sublime
import sublime_plugin
import Default.exec

from . import project_settings as ps
from . import cmake_client

imp.reload(ps)
imp.reload(cmake_client)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideRunCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):

        print('build called with {} {}'.format(args, kwargs))
