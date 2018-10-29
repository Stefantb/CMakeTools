import imp
import time

import sublime
import sublime_plugin
import Default.exec

import CMakeIDE.project_settings as ps
import CMakeIDE.cmake_server as cmake_server

imp.reload(ps)
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

        server = cmake_server.get_cmake_server(self.window)

        if not server.is_configured:
            server.configure()
            return

        targets = server.targets()

        if kwargs.get('choose_target', False):
            self.current_target_selection = [item.id_name for item in targets]
            self.window.show_quick_panel(self.current_target_selection,
                                         self.on_new_build_target_selected)
        else:

            build_target_id = kwargs.get('build_target_id', None)
            if build_target_id is None:
                build_target_id = ps.CmakeIDESettings(self.window).current_configuration.build_target

            target = next(
                (target for target in targets if target.id_name == build_target_id), None)

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

    def on_new_build_target_selected(self, index):
        selected_target = self.current_target_selection[index]
        print('build target {} selected'.format(selected_target))

        settings = ps.CmakeIDESettings(self.window)
        current = settings.current_configuration
        if current:
            current.build_target = selected_target

            self.window.run_command("cmakeide_build", {"build_target_id": selected_target})
            settings.commit()
