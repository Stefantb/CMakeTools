import imp

import Default.exec

from . import cmake_server
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideConfigureCommand(Default.exec.ExecCommand):

    def run(self, recreate=None, **kwargs):
        server = cmake_server.get_cmake_server(self.window, recreate)
        server.configure()
