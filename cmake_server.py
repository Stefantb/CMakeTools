import json
import time
import os
import threading
import shutil
import imp

import sublime
import Default.exec

from . import compdb_api
from .check_output import check_output
from . import project_settings as ps

imp.reload(ps)


# *****************************************************************************
#
# *****************************************************************************
class Target(object):
    # possible_types_from_cmake = ['STATIC_LIBRARY', 'MODULE_LIBRARY', 'SHARED_LIBRARY', 'OBJECT_LIBRARY', 'EXECUTABLE', 'UTILITY', 'INTERFACE_LIBRARY']
    # adding an ALL type for the build all target

    __slots__ = ("name", "fullname", "id_name", "type", "build_directory", "is_rebuild")

    def __init__(self, name, fullname, id_name, type, build_directory, is_rebuild=False):
        self.name = name
        self.fullname = fullname
        self.id_name = id_name
        self.type = type
        self.build_directory = build_directory
        self.is_rebuild = is_rebuild

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Target({},{},{},{},'.format(
            self.name,
            self.fullname,
            self.type,
            self.build_directory
        )

    def __hash__(self):
        return hash(self.name)

    def build_cmd(self, cmake_binary_path):
        result = [cmake_binary_path, "--build", "."]

        if self.type != "ALL":
            result.extend(["--target", self.name])

        if self.is_rebuild:
            result.extend(["--clean-first"])

        return result


# *****************************************************************************
#
# *****************************************************************************
def get_capabilities(cmake_binary):

    try:
        command = "{cmake_binary} -E capabilities".format(
            cmake_binary=cmake_binary)
        print("running", command)
        output = check_output(command)
        return json.loads(output)

    except Exception as e:
        sublime.error_message("There was an error loading cmake's "
                              "capabilities. Your \"cmake_binary\" setting is "
                              "set to \"{}\". Please make sure that this "
                              "points to a valid cmake executable."
                              .format(cmake_binary))
        print(str(e))
        return {"error": None}


# *****************************************************************************
#
# *****************************************************************************
_servers = {}


def get_cmake_server(window, recreate=False):
    global _servers

    if recreate:
        _servers[window.id()] = None

    server = _servers.get(window.id(), None)
    if server is None:
        print('Instantiating new server for window {}'.format(window.id()))
        settings = ps.CmakeIDESettings(window)
        cmake_binary = settings.get_multilevel_setting('cmake_binary')
        server = CmakeServer(window, cmake_binary,
                             settings.current_configuration)
        _servers[window.id()] = server
    else:
        print('Server found for window {}'.format(window.id()))
    return server


# *****************************************************************************
#
# *****************************************************************************
def on_config_complete(window):
    settings = ps.CmakeIDESettings(window)
    build_folder = settings.current_configuration.build_folder_expanded(window)
    source_folder = settings.current_configuration.source_folder_expanded(
        window)
    compile_commands_path = os.path.join(build_folder, "compile_commands.json")

    if settings.get_multilevel_setting("enhance_compile_commands_with_header_info", False):
        try:
            compdb_api.enhance_compdb_with_headers(build_folder)
        except Exception as e:
            print(e)

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
    if settings.get_multilevel_setting("copy_compile_commands_to_project_path", False):
        destination = os.path.join(source_folder, "compile_commands.json")
        shutil.copyfile(compile_commands_path, destination)


# *****************************************************************************
#
# *****************************************************************************
class CmakeServer(Default.exec.ProcessListener):

    _BEGIN_TOKEN = '[== "CMake Server" ==['
    _END_TOKEN = ']== "CMake Server" ==]'
    encoding = "utf-8"  # Implement listener protocol

    def __init__(self,
                 window,
                 cmake_binary_path,
                 cmake_configuration):

        self.window = window
        self.cmake_binary_path = cmake_binary_path
        self.cmake_configuration = cmake_configuration
        self.server_capabilities = get_capabilities(self.cmake_binary_path)

        self.is_configured = False
        self.is_configuring = False
        self.is_building = False  # maintained by CmakeBuildCommand
        self.data_parts = ''
        self.inside_json_object = False
        self._targets = None

        self._set_protocol(self.server_capabilities)
        self._start_connection()

    # *****************************************************************************
    #   Public API
    # *****************************************************************************
    def targets(self):
        return self._targets

    def configure(self):
        self._configure()
    # is_building
    # is_configured

    # *****************************************************************************
    #
    # *****************************************************************************
    def _start_connection(self):
        cmd = [self.cmake_binary_path, "-E", "server"]
        env = {}
        experimental = True
        debug = True
        if experimental:
            cmd.append("--experimental")
        if debug:
            cmd.append("--debug")
        self.proc = Default.exec.AsyncProcess(
            cmd=cmd, shell_cmd=None, listener=self, env=env)

    def _set_protocol(self, server_capabilities):
        version = server_capabilities.get('version')
        if version["major"] >= 3 and version["minor"] >= 11:
            self.protocol = (1, 2)
        elif version["major"] >= 3 and version["minor"] >= 10:
            self.protocol = (1, 1)
        else:
            self.protocol = (1, 0)
        # print("Chosen protocol is", self.protocol)

    def __del__(self):
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
                    self._process_chunk(self.data_parts)
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
                        self._process_chunk(self.data_parts)
                        self.data_parts = ""
                        self.inside_json_object = False

    def _process_chunk(self, data):
        d = json.loads(data)
        self._process_data(d)

    def _send(self, data):
        while not hasattr(self, "proc"):
            time.sleep(0.01)  # terrible hack :(
        self.proc.proc.stdin.write(data)
        self.proc.proc.stdin.flush()

    def _send_dict(self, thedict):
        data = b'\n[== "CMake Server" ==[\n'
        data += json.dumps(thedict).encode('utf-8') + b'\n'
        data += b'\n]== "CMake Server" ==]\n'
        self._send(data)

    def _send_handshake(self):
        self.protocoldict = {
            "major": self.protocol[0],
            "minor": self.protocol[1],
            "isExperimental": True
        }
        self._send_dict({
            "type": "handshake",
            "protocolVersion": self.protocoldict,
            "sourceDirectory": self.cmake_configuration.source_folder_expanded(self.window),
            "buildDirectory": self.cmake_configuration.build_folder_expanded(self.window),
            "generator": self.cmake_configuration.generator  # ,
            # "platform": self.cmake.platform,
            # "toolset": self.cmake.toolset
        })

    def _set_global_setting(self, key, value):
        self._send_dict({"type": "setGlobalSettings", key: value})

    def _get_configure_arguments(self):
        ovr = []
        for key, value in self.cmake_configuration.arguments.items():
            if type(value) is bool:
                value = "ON" if value else "OFF"
            ovr.append("-D{}={}".format(key, value))
        return ovr

    def _configure(self):
        if self.is_configuring:
            return
        self.is_configuring = True
        self.bad_configure = False

        window = self.window
        view = window.create_output_panel("cmake.configure", True)
        view.settings().set("result_file_regex", r'CMake\s(?:Error|Warning)'
                            r'(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:')
        view.settings().set("result_base_dir",
                            self.cmake_configuration.source_folder_expanded(self.window))
        view.set_syntax_file(
            "Packages/CMakeIDE/Syntax/Configure.sublime-syntax")
        window.run_command("show_panel", {"panel": "output.cmake.configure"})

        self._send_dict(
            {"type": "configure", "cacheArguments": self._get_configure_arguments()})

    def _compute(self):
        self._send_dict({"type": "compute"})

    def _codemodel(self):
        self._send_dict({"type": "codemodel"})

    def _cache(self):
        self._send_dict({"type": "cache"})

    def _file_system_watchers(self):
        self._send_dict({"type": "fileSystemWatchers"})

    def _cmake_inputs(self):
        self._send_dict({"type": "cmakeInputs"})

    def _global_settings(self):
        self._send_dict({"type": "globalSettings"})

    def _process_data(self, thedict):
        t = thedict.pop("type")
        if t == "hello":
            supported_protocols = thedict.pop("supportedProtocolVersions")
            # print(supported_protocols)
            self._send_handshake()
        elif t == "reply":
            self._handle_reply(thedict)
        elif t == "error":
            self._receive_error(thedict)
        elif t == "progress":
            self._receive_progress(thedict)
        elif t == "message":
            self._receive_message(thedict)
        elif t == "signal":
            self._receive_signal(thedict)
        else:
            print('CMakeIDE: Received unknown type "{}"'.format(t))
            print(thedict)

    def _handle_reply(self, thedict):
        reply = thedict["inReplyTo"]
        if reply == "handshake":
            self._handle_reply_handshake(thedict)
        elif reply == "setGlobalSettings":
            self._handle_reply_setGlobalSettings(thedict)
        elif reply == "configure":
            self._handle_reply_configure(thedict)
        elif reply == "compute":
            self._handle_reply_compute(thedict)
        elif reply == "fileSystemWatchers":
            self._dump_to_new_view(thedict, "File System Watchers")
        elif reply == "cmakeInputs":
            self._dump_to_new_view(thedict, "CMake Inputs")
        elif reply == "globalSettings":
            self._handle_reply_globalSettings(thedict)
        elif reply == "codemodel":
            self._handle_reply_codemodel(thedict)
        elif reply == "cache":
            self._handle_reply_cache(thedict)
        else:
            print("CMakeIDE: received unknown reply type:", reply)

    def _handle_reply_handshake(self, thedict) -> None:
        self.window.status_message(
            "CMake server protocol {}.{}, handshake is OK".format(
                self.protocoldict["major"], self.protocoldict["minor"]))
        self.configure()

    def _handle_reply_setGlobalSettings(self, thedict) -> None:
        self.window.status_message("Global CMake setting is modified")

    def _handle_reply_compute(self, thedict) -> None:
        self.window.status_message("Project is generated")
        self.is_configuring = False
        self._codemodel()

    def _handle_reply_configure(self, thedict) -> None:
        if self.bad_configure:
            self.is_configuring = False
            self.window.status_message(
                "Some errors occured during configure!")
        else:
            self.window.status_message("Project is configured")

    def _handle_reply_globalSettings(self, thedict) -> None:
        thedict.pop("cookie")
        thedict.pop("capabilities")
        self.items = []
        self.types = []
        for k, v in thedict.items():
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

    def _handle_reply_codemodel(self, codemodel_data) -> None:

        self._targets = []
        configurations = codemodel_data.get('configurations')

        for configuration in configurations:

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
                    self._targets.append(Target(name=target_name,
                                                fullname=target_fullname,
                                                id_name=target_name,
                                                type=target_type,
                                                build_directory=target_build_directory))

                    self._targets.append(Target(name=target_name,
                                                fullname=target_fullname,
                                                id_name=target_name + '-rebuild',
                                                type=target_type,
                                                build_directory=target_build_directory,
                                                is_rebuild=True))

        # Then a build all target
        self._targets.append(Target(name='BUILD ALL',
                                    fullname='BUILD ALL',
                                    id_name="BUILD ALL",
                                    type='ALL',
                                    build_directory=self.cmake_configuration.build_folder_expanded(self.window)))

        # Then a clean all target
        self._targets.append(Target(name='clean',
                                    fullname='clean',
                                    id_name='clean',
                                    type='CLEAN',
                                    build_directory=self.cmake_configuration.build_folder_expanded(self.window)))

        on_config_complete(self.window)
        self.is_configured = True

    def _handle_reply_cache(self, thedict) -> None:
        cache = thedict.pop("cache")
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

    def _receive_error(self, thedict):
        reply = thedict["inReplyTo"]
        msg = thedict["errorMessage"]
        if reply in ("configure", "compute"):
            self.window.status_message(msg)
            if self.is_configuring:
                self.is_configuring = False
        else:
            sublime.error_message("{} (in reply to {})".format(msg, reply))

    def _receive_progress(self, thedict):
        view = self.window.active_view()
        minimum = thedict["progressMinimum"]
        maximum = thedict["progressMaximum"]
        current = thedict["progressCurrent"]
        if maximum == current:
            view.erase_status("cmake_" + thedict["inReplyTo"])
            if thedict["inReplyTo"] == "configure" and not self.bad_configure:
                self._compute()
        else:
            status = "{0} {1:.0f}%".format(
                thedict["progressMessage"],
                100.0 * (float(current) / float(maximum - minimum)))
            view.set_status("cmake_" + thedict["inReplyTo"], status)

    def _receive_message(self, thedict):
        window = self.window
        if thedict["inReplyTo"] in ("configure", "compute"):
            name = "cmake.configure"
        else:
            name = "cmake." + thedict["inReplyTo"]
        view = window.find_output_panel(name)
        assert view

        # settings = sublime.load_settings("CMakeIDE.sublime-settings")
        # if settings.get("server_configure_verbose", False):
        if True:
            window.run_command("show_panel",
                               {"panel": "output.{}".format(name)})
        view.run_command("append", {
            "characters": thedict["message"] + "\n",
            "force": True,
            "scroll_to_end": True
        })
        self._check_for_errors_in_configure(view)

    _signal_lock = threading.Lock()

    def _receive_signal(self, thedict):
        with self.__class__._signal_lock:
            if (thedict["name"] == "dirty" and not self.is_configuring
                    and not self.is_building):
                self.configure()
            else:
                print("received signal")
                print(thedict)

    def _dump_to_new_view(self, thedict, name):
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name(name)
        thedict.pop("inReplyTo")
        thedict.pop("cookie")
        view.run_command("append", {
            "characters": json.dumps(thedict, indent=2),
            "force": True
        })
        view.set_read_only(True)
        view.set_syntax_file("Packages/JavaScript/JSON.sublime-syntax")

    def _check_for_errors_in_configure(self, view):
        scopes = view.find_by_selector("invalid.illegal")
        errorcount = len(scopes)
        if errorcount > 0:
            self.bad_configure = True
            self.window.run_command("show_panel",
                                    {"panel": "output.cmake.configure"})


# Capabilities
# {
#     "serverMode":true,
#     "version":{
#         "string":"3.12.2",
#         "patch":2,
#         "major":3,
#         "suffix":"",
#         "isDirty":false,
#         "minor":12
#     },
#     "generators":[
#         {
#             "platformSupport":false,
#             "name":"Ninja",
#             "toolsetSupport":false,
#             "extraGenerators":[
#                 "CodeBlocks",
#                 "CodeLite",
#                 "Sublime Text 2",
#                 "Kate",
#                 "Eclipse CDT4"
#             ]
#         },
#         {
#             "platformSupport":false,
#             "name":"Watcom WMake",
#             "toolsetSupport":false,
#             "extraGenerators":[]
#         },
#         {
#             "platformSupport":false,
#             "name":"Unix Makefiles",
#             "toolsetSupport":false,
#             "extraGenerators":[
#                 "CodeBlocks",
#                 "CodeLite",
#                 "Sublime Text 2",
#                 "Kate",
#                 "Eclipse CDT4"
#             ]
#         }
#     ]
# }


# print('_handle_reply_codemodel {}'.format(codemodel_data))
# {
#     "configurations":[
#         {
#             "name":"",
#             "projects":[
#                 {
#                     "name":"sml-test",
#                     "targets":[
#                         {
#                             "linkerLanguage":"CXX",
#                             "name":"packml_unit",
#                             "linkLibraries":"-lappbase -lstorageconfig -lstoragestate -lplutoexcept",
#                             "type":"EXECUTABLE",
#                             "buildDirectory":"/home/stefantb/.config/sublime-text-3/Packages/CMakeIDE/cmake-build-MyConfig-Debug",
#                             "artifacts":[
#                                 "/home/stefantb/.config/sublime-text-3/Packages/CMakeIDE/cmake-build-MyConfig-Debug/packml_unit"
#                             ],
#                             "sourceDirectory":"/home/stefantb/Dev/packml_unit/packml_unit",
#                             "fullName":"packml_unit",
#                             "fileGroups":[
#                                 {
#                                     "compileFlags":"  -O2 -Wall -Wextra -Werror -pedantic -pedantic-errors --sysroot= -ggdb -O0 -DDEBUG -W -D_GLIBCXX_USE_CXX11_ABI=0 -pthread",
#                                     "sources":[
#                                         "packml_unit.cpp",
#                                         "packml_unit_impl.cpp"
#                                     ],
#                                     "isGenerated":false,
#                                     "includePath":[
#                                         {
#                                             "path":"/home/stefantb/Dev/packml_unit/packml_unit"
#                                         }
#                                     ],
#                                     "language":"CXX"
#                                 }
#                             ],
#                             "isGeneratorProvided":false
#                         }
#                     ],
#                     "minimumCMakeVersion":"3.10",
#                     "buildDirectory":"/home/stefantb/.config/sublime-text-3/Packages/CMakeIDE/cmake-build-MyConfig-Debug",
#                     "sourceDirectory":"/home/stefantb/Dev/packml_unit/packml_unit",
#                     "hasInstallRule":false
#                 }
#             ]
#         }
#     ],
#     "cookie":"",
#     "inReplyTo":"codemodel"
# }
