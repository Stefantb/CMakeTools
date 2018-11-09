import json
import os
import shutil
import imp
import copy

import sublime

from . import compdb_api
from . import project_settings as ps
from . import build_tools
from .check_output import check_output
from . import cmake_protocol as protocol
from . import logging

imp.reload(ps)
imp.reload(build_tools)
imp.reload(logging)
imp.reload(protocol)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
def handle_compilation_database(window):
    settings = ps.CmakeIDESettings(window)
    build_folder = settings.current_configuration.build_folder_expanded(window)
    source_folder = settings.current_configuration.source_folder_expanded(
        window)
    compile_commands_path = os.path.join(build_folder, "compile_commands.json")

    if settings.get_multilevel_setting("enhance_compile_commands_with_header_info", False):
        try:
            compdb_api.enhance_compdb_with_headers(build_folder)
        except Exception as e:
            logger.info(e)

    #
    data = window.project_data()
    if settings.get_multilevel_setting("auto_update_EasyClangComplete_compile_commands_location", False):
        data["settings"]["ecc_flags_sources"] = [
            {
                "file": "compile_commands.json",
                "search_in": build_folder
            }]
    window.set_project_data(data)

    #
    copy_to_path = settings.get_multilevel_setting("copy_compile_commands_dir", '', expand=True)
    if copy_to_path:
        destination = os.path.join(copy_to_path, "compile_commands.json")
        shutil.copyfile(compile_commands_path, destination)


# *****************************************************************************
#
# *****************************************************************************
class CMakeClient:
    """docstring for CMakeClient"""

    _handlers = {}

    def __init__(self, window, recreate=False):
        self.window = window
        self.handler = CMakeClient.get_protocl_handler(window, recreate)
        self.handler.on_code_model_ready = self._on_code_model_ready
        self.handler.start_connection()

    @staticmethod
    def get_capabilities(cmake_binary):

        try:
            command = "{cmake_binary} -E capabilities".format(
                cmake_binary=cmake_binary)
            logger.info("running", command)
            output = check_output(command)
            return json.loads(output)

        except Exception as e:
            sublime.error_message("There was an error loading cmake's "
                                  "capabilities. Your \"cmake_binary\" setting is "
                                  "set to \"{}\". Please make sure that this "
                                  "points to a valid cmake executable."
                                  .format(cmake_binary))
            logger.info(str(e))
            return {"error": None}

    @classmethod
    def get_protocl_handler(cls, window, recreate=False) -> protocol.CMakeProtocolHandler:
        if recreate:
            cls._handlers[window.id()] = None

        handler = cls._handlers.get(window.id(), None)
        if handler is None:
            logger.info('Instantiating new handler for window {}'.format(window.id()))
            settings = ps.CmakeIDESettings(window)
            cmake_binary = settings.get_multilevel_setting('cmake_binary')

            source_directory = settings.current_configuration.source_folder_expanded(
                window)
            build_directory = settings.current_configuration.build_folder_expanded(
                window)
            generator = settings.current_configuration.generator

            arguments = settings.current_configuration.arguments
            cfgstr = settings.current_configuration.configuration

            for item in ['Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel']:
                if item.lower() == cfgstr.lower():
                    if arguments.get('CMAKE_BUILD_TYPE', False):
                        logger.warn('CMAKE_BUILD_TYPE gets overriden according to the configuration setting')
                    arguments['CMAKE_BUILD_TYPE'] = item
                    break

            configuration = protocol.CMakeConfiguration(cmake_binary=cmake_binary,
                                                        source_folder=source_directory,
                                                        build_folder=build_directory,
                                                        generator=generator,
                                                        arguments=arguments
                                                        )

            handler = protocol.CMakeProtocolHandler(window, configuration)
            cls._handlers[window.id()] = handler
        else:
            logger.info('handler found for window {}'.format(window.id()))

        return handler

    def configure(self):
        self.handler.configure()

    def _on_code_model_ready(self, cmake_targets, config):

        build_tools.create_build_targets(cmake_targets, config)

        handle_compilation_database(self.window)
