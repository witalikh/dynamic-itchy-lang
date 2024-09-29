"""
DI = Dynamic Itchy
"""


class DIBaseException(BaseException):
    def __init__(self, line: int, pos: int, msg):
        self.line = line
        self.pos = pos
        self.msg = msg

    def __str__(self):
        return f"Error in line {self.line}, char {self.pos} (approximate position): {self.msg}"


class DIStaticSyntaxError(DIBaseException):
    pass


class DIRuntimeSyntaxError(DIBaseException):
    pass


class DIZeroDivisionError(DIBaseException):
    pass


class DIIndexError(DIBaseException):
    pass


class DITypeError(DIBaseException):
    pass


class DIValueError(DIBaseException):
    pass


class DIRuntimeError(DIBaseException):
    pass


class DINameError(DIBaseException):
    pass
