import imp

import Default.exec

from . import project_settings as ps
from . import cmake_client
from . import clear_cache
imp.reload(cmake_client)
imp.reload(ps)

def clear_cache_files(window):
    settings = ps.CmakeIDESettings(window)
    build_folder = settings.current_configuration.build_folder_expanded(window)

    files_to_remove, dirs_to_remove = clear_cache.find_removals(build_folder)

    clear_cache.remove(files_to_remove, dirs_to_remove)

# *****************************************************************************
#
# *****************************************************************************
class CmakeideConfigureCommand(Default.exec.ExecCommand):

    def run(self, reconfigure=None, **kwargs):

        if reconfigure:
            client = cmake_client.CMakeClient(self.window, recreate=True)
            clear_cache_files(self.window)
        else:
            client = cmake_client.CMakeClient(self.window)

        client.configure()
