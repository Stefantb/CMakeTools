import imp
import time

import sublime
import sublime_plugin
import Default.exec

from . import project_settings as ps
from . import cmake_server

imp.reload(ps)
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideRunCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):

        print('build called with {} {}'.format(args, kwargs))
