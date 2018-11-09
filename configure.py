import imp

import Default.exec

from . import cmake_client
from . import clear_cache

imp.reload(cmake_client)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideConfigureCommand(Default.exec.ExecCommand):

    def run(self, reconfigure=None, **kwargs):

        if reconfigure:
            client = cmake_client.CMakeClient(self.window, recreate=True)
            clear_cache.clear_cache(self.window, with_confirmation=False)
        else:
            client = cmake_client.CMakeClient(self.window)

        client.configure()
