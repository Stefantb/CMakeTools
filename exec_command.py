import imp

import Default.exec

from . import build_tools
from . import logging

imp.reload(build_tools)
imp.reload(logging)


# *****************************************************************************
#
# *****************************************************************************
logger = logging.get_logger(__name__)


# *****************************************************************************
# A wrapper that tries to make sure we dont thrash while building
# *****************************************************************************
class CmaketoolsExecCommand(Default.exec.ExecCommand):

    def run(self, id=None, **kwargs):

        logger.info('cmaketools_exec called with {}'.format(kwargs))

        if build_tools.is_building():
            logger.info('Already building so we will wait')
            return

        build_tools.set_is_building(True)
        super().run(**kwargs)

    def on_finished(self, proc):
        logger.info('cmaketools_exec finished')
        super().on_finished(proc)
        build_tools.set_is_building(False)
