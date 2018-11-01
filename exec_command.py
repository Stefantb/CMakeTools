import imp

import Default.exec

from . import build_tools

imp.reload(build_tools)


# *****************************************************************************
# A wrapper that tries to make sure we dont thrash while building
# *****************************************************************************
class CmakeideExecCommand(Default.exec.ExecCommand):

    def run(self, id=None, **kwargs):

        print('cmakeide_exec called with {}'.format(kwargs))

        if build_tools.is_building():
            print('Already building so we will wait')
            return

        build_tools.set_is_building(True)
        super().run(**kwargs)

    def on_finished(self, proc):
        print('cmakeide_exec finished')
        super().on_finished(proc)
        build_tools.set_is_building(False)
