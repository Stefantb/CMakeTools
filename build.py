import imp

import sublime_plugin

from . import project_settings as ps
from . import build_tools
from . import logging

imp.reload(ps)
imp.reload(build_tools)
imp.reload(logging)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class CmaketoolsBuildCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        logger.info('build called with {} {}'.format(args, kwargs))

        settings = ps.Settings(self.window)

        targets = build_tools.read_build_targets(
            settings.current_configuration.build_folder_expanded(self.window))

        if kwargs.get('choose_target', False):
            self.current_target_selection = [
                item.get('id') for item in targets]
            self.window.show_quick_panel(self.current_target_selection,
                                         self.on_new_build_target_selected)
        else:

            build_target_id = kwargs.get(
                'build_target_id', settings.current_configuration.build_target)

            target = next(
                (target for target in targets if target.get('id') == build_target_id), None)

            if target:
                self.window.run_command(
                    "cmaketools_exec", target
                )
            else:
                logger.info('build target {} not found'.format(build_target_id))
                logger.info('build targets {}'.format(targets))
                self.window.run_command(
                    "cmaketools_build", {'choose_target': True}
                )

    def on_new_build_target_selected(self, index):
        selected_target = self.current_target_selection[index]
        logger.info('build target {} selected'.format(selected_target))

        settings = ps.Settings(self.window)
        current = settings.current_configuration
        if current:
            current.build_target = selected_target

            self.window.run_command(
                "cmaketools_build", {"build_target_id": selected_target})

            logger.info(settings.current_configuration.build_target)
            settings.commit()
