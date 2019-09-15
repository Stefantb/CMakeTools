class OutputPanel:

    def __init__(self, window):
        self.window = window

        self.name = "cmake.configure"

        self.view = window.create_output_panel(self.name, True)
        self.view.settings().set("result_file_regex", r'CMake\s(?:Error|Warning)'
                            r'(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:')

        self.view.set_syntax_file(
            "Packages/CMakeTools/Syntax/Configure.sublime-syntax")

    def show(self):
        self.window.run_command("show_panel",
                                {"panel": "output.{}".format(self.name)})

    def append(self, message):

        self.show()

        self.view.run_command("append", {
            "characters": message + "\n",
            "force": True,
            "scroll_to_end": True
        })
