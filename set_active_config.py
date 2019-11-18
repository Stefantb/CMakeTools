import imp

import sublime_plugin

from . import project_settings as ps
from . import cmake_client
from . import logging

imp.reload(ps)
imp.reload(cmake_client)
imp.reload(logging)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class NewConfigNameHandler(sublime_plugin.TextInputHandler):

    def __init__(self, settings):
        super(NewConfigNameHandler, self).__init__()
        self.settings = settings
        self.current_ids = [item.unique_id for item in self.settings.configurations]
        self.current_names = [item.name for item in self.settings.configurations]
        self.new_config_name = 'empty'

    def placeholder(self):
        return "New config name"

    def initial_text(self):
        return 'MyConfig'

    def preview(self, name):
        if name not in self.current_names:
            return 'New config name: {}'.format(name)
        else:
            ret = []
            for uid in self.current_ids:
                print('name {}'.format(name))
                print('uid {}'.format(uid))
                if name in uid:
                    ret.append(uid)
            return 'We already have: ' + ', '.join(ret)

    def confirm(self, name):
        self.new_config_name = name

    def next_input(self, args):
        logger.info('next_input {} for {}'.format(args, self.name()))
        return ConfigTypeHandler(self.settings, self.new_config_name)

    def name(self):
        return 'new_config_name'


# *****************************************************************************
#
# *****************************************************************************
class ConfigTypeHandler(sublime_plugin.ListInputHandler):

    def __init__(self, settings, config_name):
        super(ConfigTypeHandler, self).__init__()
        self.settings = settings
        self.config_name = config_name
        self.current_ids = [item.unique_id for item in self.settings.configurations]
        self.config_selection = ['Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel']

    def list_items(self):
        return self.config_selection

    def validate(self, config):
        return ps.unique_configuration_id(self.config_name, config) not in self.current_ids

    def confirm(self, config):
        newitem = dict(name=self.config_name,
                       arguments={'CMAKE_EXPORT_COMPILE_COMMANDS': True},
                       configuration=config,
                       generator='Unix Makefiles',
                       build_folder='${folder}/cmake-build-{name}-{configuration}',
                       source_folder='${folder}'
                       )

        self.settings.configurations += [ps.Configuration(data=newitem)]
        self.settings.commit()

        logger.info('confirm {}'.format(newitem))
        return True

    def preview(self, config):
        if ps.unique_configuration_id(self.config_name, config) not in self.current_ids:
            return 'New config {} {}'.format(self.config_name, config)
        else:
            return '{} {} exists already !'.format(self.config_name, config)

    def next_input(self, args):
        logger.info('next_input {} for {}'.format(args, self.name()))
        return None

    def name(self):
        return 'new_config_type'


# *****************************************************************************
#
# *****************************************************************************
class ActiveConfigHandler(sublime_plugin.ListInputHandler):

    def __init__(self, settings):
        super(ActiveConfigHandler, self).__init__()
        self.settings = settings
        self.current_config = settings.current_configuration_id
        self.current_config_selection = [item.unique_id for item in self.settings.configurations if item.unique_id != self.current_config] + ['Create New']

    def list_items(self):
        return self.current_config_selection

    def preview(self, value):
        if value == 'Create New':
            return 'Create a new config'
        else:
            return 'Replace \'{}\' with \'{}\''.format(self.current_config, value)

    def next_input(self, args):
        logger.info('next_input {} for {}'.format(args, self.name()))
        if args[self.name()] == 'Create New':
            return NewConfigNameHandler(self.settings)
        return None

    def name(self):
        return 'active_config_id'


# *****************************************************************************
#
# *****************************************************************************
class CmaketoolsSetActiveConfigCommand(sublime_plugin.WindowCommand):

    def __init__(self, text):
        super(CmaketoolsSetActiveConfigCommand, self).__init__(text)

    def input(self, *args):
        logger.info(args)
        settings = ps.Settings(self.window)
        return ActiveConfigHandler(settings)

    def run(self, *args, active_config_id=None, new_config_name=None, new_config_type=None, **kwargs):
        if not active_config_id:
            logger.info('Gather input by other means')
            return

        if new_config_name is not None:
            active_config_id = ps.unique_configuration_id(new_config_name, new_config_type)

        logger.info('Ok then {}'.format(active_config_id))

        settings = ps.Settings(self.window)
        settings.current_configuration_id = active_config_id

        curr = settings.current_configuration
        logger.info(curr.build_folder_expanded(self.window))
        settings.commit()

        client = cmake_client.CMakeClient(self.window, recreate=True)
        client.configure()
