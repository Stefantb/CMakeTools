import json
import time
import imp
# import itertools
import os

import sublime
import Default.exec

from . import logging
from .cmake_configuration import CMakeConfiguration
from .output_panel import OutputPanel
from .cmake_target import CMakeTarget


# *****************************************************************************
#
# *****************************************************************************
imp.reload(logging)
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class CMakeServerClient(Default.exec.ProcessListener):

    _BEGIN_TOKEN = '[== "CMake Server" ==['
    _END_TOKEN = ']== "CMake Server" ==]'
    encoding = "utf-8"  # Implement listener protocol

    def __init__(self,
                 window,
                 cmake_configuration: CMakeConfiguration):

        self.window = window
        self.cmake_configuration = cmake_configuration

        self.cmake_binary_path = cmake_configuration.cmake_binary
        self.on_code_model_ready = None

        self.is_ready = False
        self.is_working = False
        self.data_parts = ''
        self.inside_json_object = False

        self.config_output = OutputPanel(self.window)

        logger.debug('CMakeServerClient initialized with {}'.format(cmake_configuration))


    # *****************************************************************************
    #   Public API
    # *****************************************************************************
    def start_connection(self):
        cmd = [self.cmake_binary_path, "-E",
               "server", "--experimental", "--debug"]

        logger.debug('Starting server with: {}'.format(cmd))

        self.config_output.append('=' * 80)
        self.config_output.append(' '.join(cmd))

        self.proc = Default.exec.AsyncProcess(
            cmd=cmd, shell_cmd=None, listener=self, env={})

    def configure(self):
        if not self.is_ready:
            logger.debug('server not ready to take commands')
            return
        if self.is_working:
            logger.debug('server already working')
            return
        self._configure()

    def global_settings(self):
        self._global_settings()

    def cmake_inputs(self):
        self._cmake_inputs()

    def file_system_watchers(self):
        self._file_system_watchers()

    def cache(self):
        self._cache()

    # *****************************************************************************
    #
    # *****************************************************************************
    def __del__(self):
        logger.debug('CMakeServerClient.__del__()')
        if self.proc:
            self.proc.kill()

    # Override for ProcessListener
    def on_finished(self, _):
        self.window.status_message("CMake Server has quit (exit code {})"
                                   .format(self.proc.exit_code()))

    # Override for ProcessListener
    def on_data(self, _, data):
        if data.startswith("CMake Error:"):
            sublime.error_message(data)
            return

        while data:
            if self.inside_json_object:
                end_index = data.find(self.__class__._END_TOKEN)
                if end_index == -1:
                    # This is okay, wait for more data.
                    self.data_parts += data
                    data = None
                else:
                    self.data_parts += data[0:end_index]
                    data = data[end_index + len(self.__class__._END_TOKEN):]
                    self._process_text_chunk(self.data_parts)
                    self.data_parts = ""
                    self.inside_json_object = False
            else:  # not inside json object
                begin_index = data.find(self.__class__._BEGIN_TOKEN)
                if begin_index == -1:
                    data = None
                else:
                    begin_token_end = begin_index + len(
                        self.__class__._BEGIN_TOKEN)
                    end_index = data.find(self.__class__._END_TOKEN,
                                          begin_token_end)
                    if end_index == -1:
                        # This is okay, wait for more data.
                        self.data_parts += data[begin_token_end:]
                        data = None
                        self.inside_json_object = True
                    else:
                        self.data_parts += data[begin_token_end:end_index]
                        data = data[
                            end_index + len(self.__class__._END_TOKEN):]
                        self._process_text_chunk(self.data_parts)
                        self.data_parts = ""
                        self.inside_json_object = False

    # *****************************************************************************
    #  Send
    # *****************************************************************************
    # @logging.log_method_call(logger)
    def _send_text(self, json_data):
        while not hasattr(self, "proc"):
            logger.debug('terrible hack :(')
            time.sleep(0.01)
        self.proc.proc.stdin.write(json_data)
        self.proc.proc.stdin.flush()

    def _send_dict(self, data):
        json_data = b'\n[== "CMake Server" ==[\n'
        json_data += json.dumps(data).encode('utf-8') + b'\n'
        json_data += b'\n]== "CMake Server" ==]\n'
        self._send_text(json_data)

    def _handshake(self):
        protocoldict = {
            "major": 1,
            "isExperimental": True
        }
        self._send_dict({
            "type": "handshake",
            "protocolVersion": protocoldict,
            "sourceDirectory": self.cmake_configuration.source_folder,
            "buildDirectory": self.cmake_configuration.build_folder,
            "generator": self.cmake_configuration.generator  # ,
            # "platform": self.cmake.platform,
            # "toolset": self.cmake.toolset
        })

    def _configure(self):
        self.is_working = True
        self.bad_configure = False

        def get_configure_arguments(cmake_configuration):
            formatted = []
            for key, value in cmake_configuration.arguments.items():
                if type(value) is bool:
                    value = "ON" if value else "OFF"
                formatted.append("-D{}={}".format(key, value))
            return formatted

        args = get_configure_arguments(self.cmake_configuration)

        self.config_output.append('cacheArguments:\n{}\n'.format('\n'.join(args)))
        self._send_dict(
            {"type": "configure", "cacheArguments": args})

    def _compute(self):
        self.is_working = True
        self._send_dict({"type": "compute"})

    def _codemodel(self):
        self.is_working = True
        self._send_dict({"type": "codemodel"})

    def _cache(self):
        self._send_dict({"type": "cache"})

    def _file_system_watchers(self):
        self._send_dict({"type": "fileSystemWatchers"})

    def _cmake_inputs(self):
        self._send_dict({"type": "cmakeInputs"})

    def _global_settings(self):
        self._send_dict({"type": "globalSettings"})

    def _set_global_setting(self, key, value):
        self._send_dict({"type": "setGlobalSettings", key: value})

    # *****************************************************************************
    # Receive
    # *****************************************************************************
    def _process_text_chunk(self, json_data):
        data = json.loads(json_data)
        self._process_data(data)

    # @logging.log_method_call(logger)
    def _process_data(self, data):
        t = data.pop("type")
        if t == "hello":
            self._receive_hello(data)
        elif t == "reply":
            self._receive_reply(data)
        elif t == "error":
            self._receive_error(data)
        elif t == "progress":
            self._receive_progress(data)
        elif t == "message":
            self._receive_message(data)
        elif t == "signal":
            self._receive_signal(data)
        else:
            logger.debug('CMakeTools: Received unknown type "{}"'.format(t))
            logger.debug(data)

    def _receive_hello(self, data):
        self._handshake()

    def _receive_reply(self, data):
        reply = data["inReplyTo"]
        if reply == "handshake":
            self._handle_reply_handshake(data)
        elif reply == "setGlobalSettings":
            self._handle_reply_setGlobalSettings(data)
        elif reply == "configure":
            self._handle_reply_configure(data)
        elif reply == "compute":
            self._handle_reply_compute(data)
        elif reply == "fileSystemWatchers":
            self._dump_to_new_view(data, "File System Watchers")
        elif reply == "cmakeInputs":
            self._dump_to_new_view(data, "CMake Inputs")
        elif reply == "globalSettings":
            self._handle_reply_globalSettings(data)
        elif reply == "codemodel":
            self._handle_reply_codemodel(data)
        elif reply == "cache":
            self._handle_reply_cache(data)
        else:
            logger.debug("CMakeTools: received unknown reply type:", reply)

    def _receive_error(self, data):
        in_reply_to = data["inReplyTo"]
        error_message = data["errorMessage"]

        self.is_working = False
        if in_reply_to == "configure":
            self.bad_configure = True
            self.window.status_message(error_message)
            self.window.run_command("show_panel", {
                "panel": "output.cmake.configure"
            })
        elif in_reply_to == "compute":
            self.window.status_message(error_message)
            self.window.run_command("show_panel", {
                "panel": "output.cmake.configure"
            })
        else:
            sublime.error_message(
                "{} (in reply to {})".format(error_message, in_reply_to))

    def _receive_progress(self, data):
        minimum = data["progressMinimum"]
        maximum = data["progressMaximum"]
        current = data["progressCurrent"]
        in_reply_to = data["inReplyTo"]
        progress_message = data["progressMessage"]

        view = self.window.active_view()
        if maximum == current:
            view.erase_status("cmake_" + in_reply_to)
        else:
            status = "{0} {1:.0f}%".format(
                progress_message,
                100.0 * (float(current) / float(maximum - minimum))
            )
            view.set_status("cmake_" + in_reply_to, status)

    def _receive_message(self, data):

        in_reply_to = data["inReplyTo"]
        message = data["message"]

        if in_reply_to in ("configure", "compute"):
            output = self.config_output
            output.show()
            output.append(data["message"])

    def _receive_signal(self, data):
        signal_name = data["name"]
        logger.debug("received signal")
        logger.debug(data)

        if (signal_name == "dirty" and not self.is_working):
            pass
            # self.configure()

    # *****************************************************************************
    # Handle replies
    # *****************************************************************************
    def _handle_reply_handshake(self, data) -> None:
        self.is_ready = True
        self.window.status_message("")
        self._configure()

    def _handle_reply_configure(self, data) -> None:
        if self.bad_configure:
            self.window.status_message("Some errors occured during configure!")
            self.is_working = False
        else:
            self._compute()
            self.window.status_message("Project is configured")

    def _handle_reply_compute(self, data) -> None:
        self.window.status_message("Project is generated")
        self._codemodel()

    def _handle_reply_codemodel(self, codemodel_data) -> None:

        self._codemodel_data = codemodel_data
        cmake_targets = []

        configurations = codemodel_data.get('configurations')

        self.save_codemodel_to_file(configurations)

        for configuration in configurations:
            config_name = configuration.get('name')
            projects = configuration.get('projects')
            for project in projects:
                # project_name = project.get('name')
                # project_build_directory = project.get('buildDirectory')
                targets = project.get('targets')
                for target in targets:
                    target_name = target.get('name')
                    # includes extensions an such
                    target_fullname = target.get('fullName', target_name)
                    target_type = target.get('type')
                    target_build_directory = target.get('buildDirectory')
                    # target_artifacts = target.get('artifacts')
                    cmake_targets.append(CMakeTarget(name=target_name,
                                                     fullname=target_fullname,
                                                     target_type=target_type,
                                                     build_directory=target_build_directory,
                                                     configuration=config_name))
        if self.on_code_model_ready:
            self.on_code_model_ready(cmake_targets, self.cmake_configuration)
        self.is_working = False

    def _handle_reply_setGlobalSettings(self, data) -> None:
        self.window.status_message("Global CMake setting is modified")

    def _handle_reply_globalSettings(self, data) -> None:
        data.pop("cookie")
        data.pop("capabilities")
        self.items = []
        self.types = []
        for k, v in data.items():
            if type(v) in (dict, list):
                continue
            self.items.append([str(k), str(v)])
            self.types.append(type(v))
        window = self.window

        def on_done(index):
            if index == -1:
                return
            key = self.items[index][0]
            old_value = self.items[index][1]
            value_type = self.types[index]

            def on_done_input(new_value):
                if value_type is bool:
                    new_value = bool(new_value)
                self._set_global_setting(key, new_value)

            window.show_input_panel('new value for "' + key + '": ',
                                    old_value, on_done_input, None, None)

        window.show_quick_panel(self.items, on_done)

    def _handle_reply_cache(self, data) -> None:
        cache = data.pop("cache")
        self.items = []
        for item in cache:
            t = item["type"]
            if t in ("INTERNAL", "STATIC"):
                continue
            try:
                docstring = item["properties"]["HELPSTRING"]
            except Exception as e:
                docstring = ""
            key = item["key"]
            value = item["value"]
            self.items.append(
                [key + " [" + t.lower() + "]", value, docstring])

        def on_done(index):
            if index == -1:
                return
            item = self.items[index]
            key = item[0].split(" ")[0]
            old_value = item[1]

            def on_done_input(new_value):
                self.configure({key: new_value})

            self.window.show_input_panel('new value for "' + key + '": ',
                                         old_value, on_done_input, None, None)

        self.window.show_quick_panel(self.items, on_done)

    # *****************************************************************************
    # Other things
    # *****************************************************************************
    def _dump_to_new_view(self, data, name):
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name(name)
        data.pop("inReplyTo")
        data.pop("cookie")
        view.run_command("append", {
            "characters": json.dumps(data, indent=2),
            "force": True
        })
        view.set_read_only(True)
        view.set_syntax_file("Packages/JavaScript/JSON.sublime-syntax")

    def save_codemodel_to_file(self, configurations):
        output_path = os.path.join(self.cmake_configuration.build_folder, 'codemodel.json')
        with open(output_path, 'w') as f:
            f.write(json.dumps(configurations, indent=4))
