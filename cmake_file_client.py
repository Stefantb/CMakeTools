import os
import imp
import json
import re

from . import logging
from .cmake_configuration import CMakeConfiguration
from .output_panel import OutputPanel
from .check_output import check_output
from .cmake_target import CMakeTarget

# *****************************************************************************
#
# *****************************************************************************
imp.reload(logging)
logger = logging.get_logger(__name__)


REQUEST = {
    'requests': [
        {'kind': 'codemodel', 'version': 2},
        {'kind': 'cache', 'version': 2},
        {'kind': 'cmakeFiles', 'version': 1}
    ],
    'client': {}
}


# *****************************************************************************
#
# *****************************************************************************
def load_json(file_path):
    with open(file_path, 'r') as json_file:
        json_object = json.load(json_file)
        return json_object


# *****************************************************************************
#
# *****************************************************************************
def get_configure_arguments(cmake_configuration: CMakeConfiguration):
    formatted = []
    for key, value in cmake_configuration.arguments.items():
        if type(value) is bool:
            value = "ON" if value else "OFF"
        formatted.append("-D{}={}".format(key, value))

    formatted.append(
        '-G \"{}\"'.format(cmake_configuration.generator)
    )

    formatted.append(
        cmake_configuration.source_folder
    )

    return ' '.join(formatted)


# *****************************************************************************
#
# *****************************************************************************
def get_response_file(responses, file_kind):
    for response in responses:
        if response['kind'] == file_kind:
            return response['jsonFile']


# *****************************************************************************
#
# *****************************************************************************
class CMakeFileClient():
    def __init__(self,
                 output_panel: OutputPanel,
                 cmake_configuration: CMakeConfiguration):

        self.output_panel = output_panel
        self.cmake_configuration = cmake_configuration
        self.cmake_binary_path = cmake_configuration.cmake_binary

        self.api_id = 'client-cmaker-s'
        self.on_code_model_ready = None

        logger.info('CMakeFileClient initialized with {}'.format(cmake_configuration))

    def start_connection(self):
        pass

    def configure(self):

        try:
            build_dir = self.cmake_configuration.build_folder

            filename = os.path.join(build_dir, '.cmake', 'api', 'v1', 'query', self.api_id, 'query.json')
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                f.write(json.dumps(REQUEST, indent=4))

            command = "{cmake_binary} {args}".format(
                cmake_binary=self.cmake_configuration.cmake_binary,
                args=get_configure_arguments(self.cmake_configuration)
                )

            logger.info("running {}".format(command))
            output = check_output(command, cwd=build_dir)

            self.output_panel.append(output)
            self.read_replies()

        except Exception as e:
            self.output_panel.append("There was an error running cmake"
                                     "Your \"cmake_binary\" setting is "
                                     "set to \"{}\". Please make sure that this "
                                     "points to a valid cmake executable."
                                     .format(self.cmake_configuration.cmake_binary))
            logger.error(str(e))

    def read_replies(self):
        build_dir = self.cmake_configuration.build_folder
        reply_dir = os.path.join(build_dir, '.cmake', 'api', 'v1', 'reply')

        files = os.listdir(reply_dir)
        #cache-v2-3c9c1438d256b4686b73.json
        #codemodel-v2-1ca2db679e83ac6d1bfa.json
        #target-hello-Debug-77a59ee08d2a1a1be177.json
        #cmakeFiles-v1-fa489c49cd80bd793f85.json
        #index-2019-09-15T02-18-47-0510.json

        index_filter = re.compile(r'^index-\S*\.json')
        index_file_list = list(filter(index_filter.match, files))

        if not index_file_list:
            self.output_panel.append('Error: there is no reply from CMake')
            self.output_panel.append('Cannot get the code model')
            return

        # documentation states that if the files are momentarily more than one,
        # they can be lexicographically sorted
        index_file = sorted(index_file_list, reverse=True)[0]

        index_object = load_json(os.path.join(reply_dir, index_file))
        responses = index_object.get('reply', {}).get(self.api_id, {}).get('query.json', {}).get('responses', [])

        # = get_response_file(responses, 'cmakeFiles')
        # = get_response_file(responses, 'cache')
        codemodel_file = get_response_file(responses, 'codemodel')
        if not codemodel_file:
            self.output_panel.append('error reading code model')
            return
        self.read_codemodel(reply_dir, codemodel_file)

    def read_codemodel(self, reply_dir, codemodel_file):
        codemodel = load_json(os.path.join(reply_dir, codemodel_file))
        cmake_targets = []
        for config in codemodel.get('configurations', []):
            config_name = config['name']
            for target in config['targets']:
                # target['name']
                target_object = load_json(os.path.join(reply_dir, target['jsonFile']))
                cmake_tgt = CMakeTarget(
                    name=target_object['name'],
                    fullname=target_object['nameOnDisk'],
                    target_type=target_object['type'],
                    build_directory=self.cmake_configuration.build_folder,
                    configuration=config_name
                )
                cmake_targets.append(cmake_tgt)

        if self.on_code_model_ready:
            self.on_code_model_ready(cmake_targets, self.cmake_configuration)

        self.output_panel.append('done')
