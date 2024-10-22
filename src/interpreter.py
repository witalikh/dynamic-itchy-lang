"""
Combined lexer and parser
"""
from src.parser import Parser
from src.lexer import Lexer


class MiniInterpreter:

    def __init__(self) -> None:
        self.environment = {}

    def import_module(self, src: str):
        try:
            parser = Parser(Lexer(src))
            tree = parser.parse_program()
            tree.evaluate(self.environment, False)
        finally:
            pass

    def execute(self, src: str):
        try:
            parser = Parser(Lexer(src))
            tree = parser.parse_program()
            return tree.evaluate(self.environment)
        # TEMP
        finally:
            pass


class Interpreter:

    def __init__(self) -> None:
        self.environment = {}
        self.result = None

    def execute(self, src: str):
        try:
            lexer = Lexer(src)
            parser = Parser(lexer)
            tree = parser.parse_program()
            self.result = tree.evaluate(self.environment)
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
