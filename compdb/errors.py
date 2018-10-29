

class CompdbError(Exception):
    '''Base exception for errors raised by compdb'''

    def __init__(self, message, cause=None):
        super(CompdbError, self).__init__(message)
        self.cause = cause


class NotImplementedError(NotImplementedError, CompdbError):
    pass
