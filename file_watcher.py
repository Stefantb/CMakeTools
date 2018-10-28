# import os
import imp

import sublime_plugin

import CMakeIDE.project_settings as ps
import CMakeIDE.cmake_server as cmake_server

imp.reload(ps)
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class FileWatcher(sublime_plugin.EventListener):

    def on_post_save(self, view):

        if ps.CmakeIDESettings(view.window()).is_cmake_project:
            name = view.file_name()

            print('post save: {}'.format(name))

            if name.endswith("CMakeLists.txt") or \
                    name.endswith("CMakeCache.txt") or \
                    name.endswith(".sublime-project"):

                view.window().run_command("cmakeide_clear_cache",
                                          {"with_confirmation": False})

                view.window().run_command("cmakeide_configure")
