class CMakeConfiguration:

    __slots__ = ('cmake_binary', 'source_folder',
                 'build_folder', 'generator', 'arguments')

    def __init__(self, cmake_binary: str, source_folder: str,
                 build_folder: str, generator: str, arguments: dict):

        self.cmake_binary = cmake_binary
        self.source_folder = source_folder
        self.build_folder = build_folder
        self.generator = generator
        self.arguments = arguments

    def __str__(self):
        return 'CMakeConfiguration({},{},{},{},{}'.format(
            self.cmake_binary,
            self.source_folder,
            self.build_folder,
            self.generator,
            self.arguments
        )

    def __repr__(self):
        return self.__str__()
