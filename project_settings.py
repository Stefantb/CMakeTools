"""dkjdsckjds
"""

import sublime
# import sublime_plugin


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
        return self._data.get('arguments', [])

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
    def build_folder(self):
        return self._data.get('build_folder', '')

    @build_folder.setter
    def build_folder(self, build_folder):
        self._data['build_folder'] = build_folder

    def build_folder_expanded(self, window):
        build_folder = sublime.expand_variables(self.build_folder, window.extract_variables())
        return build_folder.format(**self.data())


class CmakeIDESettings():
    """docstring for CmakeIDESettings"""

    def __init__(self, window):
        self.window = window
        self.refresh()

    def refresh(self):
        """Refresh the data of this object from file, discarding changes if any"""
        self._cmake_settings = self.window.project_data().get('settings', {}).get('cmake_ide', {})

    def commit(self):
        """Commit the state of this object to file"""
        project_data = self.window.project_data()
        project_data.setdefault('settings', {}).setdefault('cmake_ide', {})
        project_data['settings']['cmake_ide'] = self._cmake_settings
        self.window.set_project_data(project_data)

    @property
    def current_configuration(self):
        """Returns none if not defined in the file"""
        return self._cmake_settings.get('current_configuration', None)

    @current_configuration.setter
    def current_configuration(self, config_name):
        """a"""
        self._cmake_settings['current_configuration'] = config_name

    @property
    def configurations(self):
        """a"""
        raw_configs = self._cmake_settings.get('configurations', [])
        return [Configuration(data=item) for item in raw_configs]

    @configurations.setter
    def configurations(self, configurations):
        """a"""
        self._cmake_settings['configurations'] = [item.data() for item in configurations]
