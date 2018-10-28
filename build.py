import imp

import sublime
import sublime_plugin
import Default.exec

import CMakeIDE.cmake_server as cmake_server
imp.reload(cmake_server)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideExecCommand(Default.exec.ExecCommand):

    def run(self, window_id, **kwargs):
        window = sublime.Window(window_id)
        self.server = cmake_server.get_cmake_server(window)
        if not self.server:
            sublime.error_message("Unable to locate server!")
            return

        if self.server.is_building:
            print('Already building so we will wait')
            return
        self.server.is_building = True
        super().run(**kwargs)

    def on_finished(self, proc):
        super().on_finished(proc)
        self.server.is_building = False


# *****************************************************************************
#
# *****************************************************************************
def get_syntax_and_regex(generator):
    file_regex = None
    syntax = None

    if sublime.platform() in ("osx", "linux"):

        file_regex = r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

        if "Makefile" in generator:
            syntax = "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
        elif "Ninja" in generator:
            syntax = "Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax"
        else:
            print("CMakeBuilder: Warning: Generator", generator,
                  "will not have syntax highlighting in the output panel.")

    elif sublime.platform() == "windows":

        if "Ninja" in generator:
            file_regex = r'^(.+)\((\d+)\):() (.+)$'
            syntax = "Packages/CMakeBuilder/Syntax/Ninja+CL.sublime-syntax"
        elif "Visual Studio" in generator:
            file_regex = (
                r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) ', r'\w+\d\d\d\d: .*) \[.*$')
            syntax = "Packages/CMakeBuilder/Syntax/Visual_Studio.sublime-syntax"
        elif "NMake" in generator:
            file_regex = r'^(.+)\((\d+)\):() (.+)$'
            syntax = "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
        else:
            print("CMakeBuilder: Warning: Generator", generator,
                  "will not have syntax highlighting in the output panel.")

    return (syntax, file_regex)


# *****************************************************************************
#
# *****************************************************************************
class CmakeideBuildCommand(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):

        print('build called with {} {}'.format(args, kwargs))

        target_name = kwargs.get('target_name', 'BUILD ALL')

        server = cmake_server.get_cmake_server(self.window)

        if server.is_configured:
            targets = server.targets()
            target = next(
                (target for target in targets if target.id_name == target_name), None)

            if target:

                syntax, file_regex = get_syntax_and_regex('Unix Makefiles')
                self.window.run_command(
                    "cmakeide_exec",
                    {
                        "window_id": self.window.id(),
                        "cmd": target.build_cmd(server.cmake_binary_path),
                        "file_regex": file_regex,
                        "syntax": syntax,
                        "working_dir": server.cmake_configuration.build_folder_expanded(self.window)
                    }
                )
        else:
            server.configure()
