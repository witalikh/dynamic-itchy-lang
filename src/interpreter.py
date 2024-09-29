"""
Combined lexer and parser
"""
from src.parser import Parser
from src.lexer import Lexer


class MiniInterpreter:

    def __init__(self) -> None:
        pass

    def execute(self, src: str):
        try:
            lexer = Lexer(src)
            parser = Parser(lexer)
            tree = parser.parse_program()
            wrapped_result = tree.evaluate({})
            result = wrapped_result.unwrap()
        # TEMP
        finally:
            pass

        # # except ExpressionError as e:
        # #     return False, str(e)
        # # except ValueError as e:
        # #     return False, str(e)
        # return result is not None, result

        return result

class Interpreter:

    def __init__(self) -> None:
        self.environment = {}
        self.result = None

    def execute(self, src: str):
        try:
            lexer = Lexer(src)
            parser = Parser(lexer)
            tree = parser.parse_program()
            wrapped_result = tree.evaluate(self.environment)
            self.result = wrapped_result.unwrap()
        # TEMP
        finally:
            pass

        # # except ExpressionError as e:
        # #     return False, str(e)
        # # except ValueError as e:
        # #     return False, str(e)
        # return result is not None, result

    def clear(self):
        self.environment.clear()
