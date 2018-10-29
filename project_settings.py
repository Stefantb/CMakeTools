import sublime


# *****************************************************************************
#
# *****************************************************************************
class Configuration():
    """docstring for Configuration"""

    def __init__(self, *, data=None):
        self._data = {}
        if data is not None:
            self._data = data

    def data(self):
        """Returns the backing dictionary"""
        return self._data

    @property
    def arguments(self):
        return self._data.get('arguments', {})

    @arguments.setter
    def arguments(self, arguments):
        self._data['arguments'] = arguments

    @property
    def configuration(self):
        return self._data.get('configuration', '')

    @configuration.setter
    def configuration(self, configuration):
        self._data['configuration'] = configuration

    @property
    def generator(self):
        return self._data.get('generator', '')

    @generator.setter
    def generator(self, generator):
        self._data['generator'] = generator

    @property
    def name(self):
        return self._data.get('name', '')

    @name.setter
    def name(self, name):
        self._data['name'] = name

    @property
    def build_target(self):
        return self._data.get('build_target', '')

    @build_target.setter
    def build_target(self, build_target):
        self._data['build_target'] = build_target

    @property
    def build_folder(self):
        return self._data.get('build_folder', '')

    @build_folder.setter
    def build_folder(self, build_folder):
        self._data['build_folder'] = build_folder

    def build_folder_expanded(self, window):
        variables = window.extract_variables()
        build_folder = sublime.expand_variables(self.build_folder, variables)
        return build_folder.format(**self.data())

    def source_folder_expanded(self, window):
        variables = window.extract_variables()
        build_folder = sublime.expand_variables(self._data.get('source_folder', ''), variables)
        return build_folder


# *****************************************************************************
#
# *****************************************************************************
class CmakeIDESettings():
    """docstring for CmakeIDESettings"""

    def __init__(self, window):
        self.window = window
        self.refresh()

    def refresh(self):
        """Refresh the data of this object from file, discarding changes if any"""
        self._data = self.window.project_data().get('settings', {}).get('cmake_ide', {})

    def commit(self):
        """Commit the state of this object to file"""
        project_data = self.window.project_data()
        project_data.setdefault('settings', {}).setdefault('cmake_ide', {})
        project_data['settings']['cmake_ide'] = self._data
        self.window.set_project_data(project_data)

    @property
    def is_cmake_project(self):
        """Returns True if settings and cmake_ide exist in the project file"""
        project_data = self.window.project_data()
        return 'cmake_ide' in project_data.setdefault('settings', {})

    @property
    def current_configuration_name(self):
        """Returns none if not defined in the file"""
        return self._data.get('current_configuration_name', None)

    @current_configuration_name.setter
    def current_configuration_name(self, config_name):
        """a"""
        self._data['current_configuration_name'] = config_name

    @property
    def configurations(self):
        """a"""
        raw_configs = self._data.get('configurations', [])
        return [Configuration(data=item) for item in raw_configs]

    @configurations.setter
    def configurations(self, configurations):
        """a"""
        self._data['configurations'] = [item.data() for item in configurations]

    def find_configuration_by_name(self, name):
        return next((x for x in self.configurations if x.name == name), None)

    @property
    def current_configuration(self) -> Configuration:
        """Returns none if not defined in the file"""
        if self.current_configuration_name:
            return self.find_configuration_by_name(self.current_configuration_name)
        else:
            return None

    @property
    def cmake_binary(self):
        """a"""
        return self._data.get('cmake_binary', '')

    def get_multilevel_setting(self, key, default=None):
        print('Getting multilevel setting for key: {}'.format(key))
        # try geting it from the current config
        value = getattr(self.current_configuration, key, None)
        if value:
            print('Found in projects current config: {}'.format(value))
            return value

        # try getting it from global project settings
        print('Not found in current configuration')
        value = getattr(self, key, None)
        if value:
            print('Found in global project: {}'.format(value))
            return value

        # try getting it from global settings
        print('Not found in global project settings')
        settings = sublime.load_settings("CMakeIDE.sublime-settings")
        value = settings.get(key, None)
        if value:
            print('Found in global settings: {}'.format(value))
            return value
        else:
            print('Gave up returning default: {}'.format(default))
            return default
