import argparse
import os
import sys
import shutil

from .compdb.backend import json
from .compdb import includedb
from .compdb import utils

from .compdb.__about__ import (__prog__, __version__)
from .compdb.backend.json import JSONCompileCommandSerializer
from .compdb.core import CompilationDatabase
from . import logging


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
#
# *****************************************************************************
class Config(object):
    def __init__(self, build_dir):
        self.build_directory_patterns = []
        self.build_dir = build_dir

    @property
    def compdb_dir(self):
        # 1. check provided as command line flag --compdb-dir=<dir>
        # 2. check provided by environment variable $COMPDB_DIR
        # 3. locate .compdb directory by walking up filesystem
        # 4. walk up filesystem
        #    - probe db from curdir: e.g. compile_commands.json
        #    - or from build directories specified in global config: e.g.
        #      build/compile_commands.json
        #
        # TODO: CompilationDatabase.probe_directory()
        return self.build_dir


# *****************************************************************************
#
# *****************************************************************************
class BackendRegistry(object):
    def __init__(self, config):
        self.config = config

    def _builtins(self):
        return [
            json.JSONCompilationDatabase,
        ]

    def iter(self):
        for backend in self._builtins():
            yield backend


# *****************************************************************************
#
# *****************************************************************************
class ListCommand():
    name = 'list'
    help_short = 'list database entries'

    def execute(self, config, output_file, argv):
        parser = argparse.ArgumentParser(
            prog='{} {}'.format(__prog__, self.name),
            description=self.help_short)
        parser.add_argument(
            '-1',
            '--unique',
            action='store_true',
            help='restrict results to a single entry per file')
        parser.add_argument(
            'files',
            metavar='file',
            nargs='*',
            help='restrict results to a list of files')
        args = parser.parse_args(argv)

        has_missing_files = False
        database = self._make_database(config)
        builder = includedb.IncludeIndexBuilder()
        included_by_database = builder.build(database)

        with JSONCompileCommandSerializer(output_file) as serializer:

            for file, compile_commands in self._gen_results(
                    database, included_by_database, args):

                has_compile_command = False
                for compile_command in compile_commands:
                    serializer.serialize(compile_command)
                    has_compile_command = True

                if file and not has_compile_command:
                    logger.error(
                        'error: {}: no such entry'.format(file),
                        file=sys.stderr)
                    has_missing_files = True
        if has_missing_files:
            sys.exit(1)

    def _make_database(self, config):
        backend_registry = BackendRegistry(config)
        database = CompilationDatabase()
        for database_cls in backend_registry.iter():
            database.register_backend(database_cls)
        try:
            if config.build_directory_patterns:
                database.add_directory_patterns(
                    config.build_directory_patterns)
            else:
                database.add_directory(config.compdb_dir)
        except models.ProbeError as e:
            logger.error(
                "{} {}: error: invalid database(s): {}".format(
                    __prog__, self.name, e),
                file=sys.stderr)
            sys.exit(1)
        return database

    def _gen_results(self, database, included_by_database, args):
        if not args.files:
            yield (None, database.get_all_compile_commands(unique=args.unique))
            yield (None, included_by_database.get_all_compile_commands())
            return
        for file in args.files:
            compile_commands = database.get_compile_commands(
                file, unique=args.unique)
            is_empty, compile_commands = utils.empty_iterator_wrap(
                compile_commands)
            if is_empty:
                path = os.path.abspath(file)
                compile_commands = included_by_database.get_compile_commands(
                    path)
            yield (file, compile_commands)


# *****************************************************************************
#
# *****************************************************************************
def enhance_compdb_with_headers(build_folder, result_folder=None):

    if result_folder is None:
        result_folder = build_folder

    config = Config(build_folder)
    command = ListCommand()

    temp_path = os.path.join(build_folder, "compile_commands_o.json")
    result_path = os.path.join(result_folder, "compile_commands.json")

    with open(temp_path, "w") as f:
        command.execute(config, f, [])

    shutil.move(src=temp_path, dst=result_path)
