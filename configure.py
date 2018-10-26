import imp

import sublime
import sublime_plugin
import Default.exec

import CMakeIDE.cmake_server as cmake_server
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideConfigureCommand(Default.exec.ExecCommand):

    def run(self):
        server = cmake_server.get_cmake_server(self.window)
        server.configure()
