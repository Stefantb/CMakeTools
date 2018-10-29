import imp

import sublime
import Default.exec

from . import cmake_server

imp.reload(cmake_server)


# *****************************************************************************
# A wrapper that tries to make sure we dont thrash while building
# *****************************************************************************
class CmakeideExecCommand(Default.exec.ExecCommand):

    def run(self, window_id, **kwargs):
        self.server = cmake_server.get_cmake_server(sublime.Window(window_id))

        if not self.server:
            sublime.error_message("Unable to locate server!")
            return

        if self.server.is_building:
            print('Already building so we will wait')
            return

        self.server.is_building = True
        super().run(**kwargs)

    def on_finished(self, proc):
        super().on_finished(proc)
        self.server.is_building = False
