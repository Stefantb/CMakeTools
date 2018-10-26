import imp

import sublime
import sublime_plugin
import Default.exec

import CMakeIDE.project_settings as ps
imp.reload(ps)
import CMakeIDE.cmake_server as cmake_server
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class NewConfigNameHandler(sublime_plugin.TextInputHandler):

    def __init__(self, settings):
        super(NewConfigNameHandler, self).__init__()
        self.settings = settings
        self.current_names = [item.name for item in self.settings.configurations]

    def placeholder(self):
        return "New config name"

    def initial_text(self):
        return 'MyConfig'

    def validate(self, text):
        return text not in self.current_names

    def confirm(self, text):
        newitem = dict(name=text,
                       arguments={'CMAKE_EXPORT_COMPILE_COMMANDS': True},
                       configuration='Debug',
                       generator='Unix Makefiles',
                       build_folder='${folder}/cmake-build-{name}-{configuration}',
                       source_folder='${folder}'
                       )


        self.settings.configurations += [ps.Configuration(data=newitem)]
        self.settings.commit()


        print('confirm {}'.format(text))
        self.new_config_name = text
        return True

    def preview(self, text):
        if text not in self.current_names:
            return 'New config name: {}'.format(text)
        else:
            return '{} exists already !'.format(text)


    def next_input(self, args):
        print('next_input {}'.format(args))
        return None

    def name(self):
        return 'new_config_name'


# *****************************************************************************
#
# *****************************************************************************
class ActiveConfigHandler(sublime_plugin.ListInputHandler):

    def __init__(self, settings):
        super(ActiveConfigHandler, self).__init__()
        self.settings = settings

    def list_items(self):
        self.current_config_selection = [item.name for item in self.settings.configurations] + ['Create New']
        return self.current_config_selection

    def preview(self, value):
        if value == 'Create New':
            return 'Create a new config'
        else:
            return 'Set {} as the active config'.format(value)

    def next_input(self, args):
        print('next_input {} for {}'.format(args, self.name()))
        if args[self.name()] == 'Create New':
            return NewConfigNameHandler(self.settings)
        return None

    def name(self):
        return 'active_config'


# *****************************************************************************
#
# *****************************************************************************
class CmakeideSetActiveConfigCommand(sublime_plugin.WindowCommand):

    def __init__(self, text):
        super(CmakeideSetActiveConfigCommand, self).__init__(text)

    def input(self, *args):
        print(args)
        settings = ps.CmakeIDESettings(self.window)
        return ActiveConfigHandler(settings)

    def run(self, *args, active_config=None, new_config_name=None, **kwargs):
        if not active_config:
            print('Gather input by other means')
            return

        if active_config == 'Create New':
            active_config = new_config_name

        print('Ok then {}'.format(active_config))

        settings = ps.CmakeIDESettings(self.window)
        settings.current_configuration_name = active_config

        curr = settings.current_configuration
        print(curr.build_folder_expanded(self.window))
        settings.commit()

        cmake_server.get_cmake_server(self.window, recreate=True)
        cmake_server.configure()
