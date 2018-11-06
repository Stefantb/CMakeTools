import imp

import sublime_plugin

from . import project_settings as ps
from . import logging
imp.reload(ps)
imp.reload(logging)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class FileWatcher(sublime_plugin.EventListener):

    def on_post_save(self, view):

        if ps.CmakeIDESettings(view.window()).is_cmake_project:
            name = view.file_name()

            logger.info('post save: {}'.format(name))

            if name.endswith("CMakeLists.txt") or \
                    name.endswith("CMakeCache.txt") or \
                    name.endswith(".cmake") or \
                    name.endswith(".sublime-project"):

                view.window().run_command("cmakeide_configure", {"reconfigure": "true"})
