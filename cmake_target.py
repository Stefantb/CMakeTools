class CMakeTarget:
    # possible_types_from_cmake:
    # 'STATIC_LIBRARY'
    # 'MODULE_LIBRARY'
    # 'SHARED_LIBRARY'
    # 'OBJECT_LIBRARY'
    # 'EXECUTABLE'
    # 'UTILITY'
    # 'INTERFACE_LIBRARY'

    __slots__ = ("name", "fullname", "type",
                 "build_directory", "configuration")

    def __init__(self, name, fullname, target_type, build_directory, configuration):
        self.name = name
        self.fullname = fullname
        self.type = target_type
        self.build_directory = build_directory
        self.configuration = configuration

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'CMakeTarget({},{},{},{},{})'.format(
            self.name,
            self.fullname,
            self.type,
            self.build_directory,
            self.configuration
        )

    def __hash__(self):
        return hash(self.name)
