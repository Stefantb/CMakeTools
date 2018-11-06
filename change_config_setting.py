# import json

import sublime_plugin

from . import cmake_client
from . import project_settings as ps
from . import logging


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
def change_generator(settings, window):
    caps = cmake_client.CMakeClient.get_capabilities(settings.get_multilevel_setting('cmake_binary'))
    generators = [generator.get('name') for generator in caps['generators']]

    def selected(id):
        logger.info(generators[id])
        settings.current_configuration.generator = generators[id]
        settings.commit()

    window.show_quick_panel(generators, selected)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideChangeConfigSettingCommand(sublime_plugin.WindowCommand):

    def run(self, *args, setting=None, **kwargs):

        if setting is None:
            return

        settings = ps.CmakeIDESettings(self.window)

        if setting == 'generator':
            change_generator(settings, self.window)
