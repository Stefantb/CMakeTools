import os
import json
import imp

import sublime

from . import logging


# *****************************************************************************
#
# *****************************************************************************
imp.reload(logging)
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
_is_building = False


def is_building():
    global _is_building
    return _is_building


def set_is_building(value):
    global _is_building
    _is_building = value


# *****************************************************************************
#
# *****************************************************************************
def build_target_cache_path(build_folder):
    return os.path.join(build_folder,
                        "CMakeFiles",
                        'cmake_tools_build_targets.json')


# *****************************************************************************
#
# *****************************************************************************
def get_syntax_and_regex(generator):
    file_regex = None
    syntax = None

    if sublime.platform() in ("osx", "linux"):

        file_regex = r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

        if "Makefile" in generator:
            syntax = "Packages/CMakeTools/Syntax/Make.sublime-syntax"
        elif "Ninja" in generator:
            syntax = "Packages/CMakeTools/Syntax/Ninja.sublime-syntax"
        else:
            logger.info("CMakeTools: Warning: Generator", generator,
                  "will not have syntax highlighting in the output panel.")

    elif sublime.platform() == "windows":

        if "Ninja" in generator:
            file_regex = r'^(.+)\((\d+)\):() (.+)$'
            syntax = "Packages/CMakeTools/Syntax/Ninja+CL.sublime-syntax"
        elif "Visual Studio" in generator:
            file_regex = (
                r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) ', r'\w+\d\d\d\d: .*) \[.*$')
            syntax = "Packages/CMakeTools/Syntax/Visual_Studio.sublime-syntax"
        elif "NMake" in generator:
            file_regex = r'^(.+)\((\d+)\):() (.+)$'
            syntax = "Packages/CMakeTools/Syntax/Make.sublime-syntax"
        else:
            logger.info("CMakeTools: Warning: Generator", generator,
                  "will not have syntax highlighting in the output panel.")

    return (syntax, file_regex)


# *****************************************************************************
#
# *****************************************************************************
def create_build_targets(cmake_targets, cmake_settings):

    build_targets = []

    syntax, file_regex = get_syntax_and_regex(cmake_settings.generator)

    for target in cmake_targets:

        cmd = [cmake_settings.cmake_binary, '--build', '.', '--target', target.name]
        build_targets.append({
            'id': target.name,
            'cmd': cmd,
            'file_regex': file_regex,
            'syntax': syntax,
            'working_dir': cmake_settings.build_folder
        })

        cmd = [cmake_settings.cmake_binary, '--build', '.', '--target', target.name, '--clean-first']
        build_targets.append({
            'id': target.name + '-rebuild',
            'cmd': cmd,
            'file_regex': file_regex,
            'syntax': syntax,
            'working_dir': cmake_settings.build_folder
        })

    # Then a build all target
    cmd = [cmake_settings.cmake_binary, '--build', '.']
    build_targets.append({
        'id': 'BUILD ALL',
        'cmd': cmd,
        'file_regex': file_regex,
        'syntax': syntax,
        'working_dir': cmake_settings.build_folder
    })

    # Then a clean all target
    cmd = [cmake_settings.cmake_binary, '--build', '.', '--target', 'clean']
    build_targets.append({
        'id': 'clean',
        'cmd': cmd,
        'file_regex': file_regex,
        'syntax': syntax,
        'working_dir': cmake_settings.build_folder
    })

    logger.info(build_targets)

    build_target_cache = build_target_cache_path(cmake_settings.build_folder)

    with open(build_target_cache, 'w') as f:
        f.write(json.dumps(build_targets, indent=2))


# *****************************************************************************
#
# *****************************************************************************
def read_build_targets(build_folder):

    data = {}
    build_target_cache = build_target_cache_path(build_folder)

    with open(build_target_cache, 'r') as f:
                data = json.load(f)

    return data
