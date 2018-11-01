import imp

import Default.exec

from . import cmake_client
imp.reload(cmake_client)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideConfigureCommand(Default.exec.ExecCommand):

    def run(self, recreate=None, **kwargs):
        client = cmake_client.CMakeClient(self.window, recreate)
        client.configure()
