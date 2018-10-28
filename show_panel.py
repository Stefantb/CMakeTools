import sublime_plugin


# *****************************************************************************
#
# *****************************************************************************
class CmakeideShowPanelCommand(sublime_plugin.WindowCommand):

    def run(self, *, panel_id, **kwargs):
        print('show: {}'.format(panel_id))

        self.window.run_command("show_panel", {"panel": "output.{}".format(panel_id)})
