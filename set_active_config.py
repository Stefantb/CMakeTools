import sublime
import sublime_plugin
import Default.exec
import CMakeIDE.project_settings as ps

import imp

imp.reload(ps)

class CmakeideSetActiveConfigCommand(Default.exec.ExecCommand):
    """Configures a CMake project with options set in the sublime project
    file."""

    # def is_enabled(self):
    #     if ps.CmakeIDESettings(self.window).current_configuration():
    #         return True

    #     return True

    def run(self):
        """Choose the active config"""
        settings = ps.CmakeIDESettings(self.window)
        existing_configs = settings.configurations

        self.current_config_selection = [item.name for item in existing_configs] + ['Create New']
        self.window.show_quick_panel(self.current_config_selection, self._on_config_selection_done)

    def _on_config_selection_done(self, index):
        if index != -1:
            chosen = self.current_config_selection[index]

            if chosen == 'Create New':
                self.create_new_configuration()
            else:
                settings = ps.CmakeIDESettings(self.window)
                settings.configuration = chosen
                settings.commit()

                curr = next((x for x in settings.configurations if x.name == chosen), None)
                print(curr.build_folder_expanded(self.window))

    def create_new_configuration(self):
        self.window.show_input_panel('New configuration Name',
                                     'MyConfig',
                                     self._on_input_panel_done, self._on_input_panel_change, self._on_input_panel_cancel)

    def _on_input_panel_done(self, text):
        print(text)

        newitem = dict(name=text,
                       arguments=['CMAKE_EXPORT_COMPILE_COMMANDS=true'],
                       configuration='Debug',
                       generator='Unix Makefiles',
                       build_folder='${folder}/cmake-build-{{name}}-{{configuration}}'
                       )

        settings = ps.CmakeIDESettings(self.window)
        print(settings.configurations)
        settings.configurations += [ps.Configuration(data=newitem)]
        settings.commit()

    def _on_input_panel_change(self, text):
        pass
        # print(text)

    def _on_input_panel_cancel(self):
        print('text input canceled')
