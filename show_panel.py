import imp

import sublime_plugin

from . import logging


# *****************************************************************************
#
# *****************************************************************************
imp.reload(logging)
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class CmaketoolsShowPanelCommand(sublime_plugin.WindowCommand):

    def run(self, *, panel_id, **kwargs):
        logger.info('show: {}'.format(panel_id))

        self.window.run_command("show_panel", {"panel": "output.{}".format(panel_id)})
