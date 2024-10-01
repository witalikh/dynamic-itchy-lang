from enum import IntEnum, auto


class Lexemes(IntEnum):
    """

    """
    EMPTY = auto()
    STRING = auto()
    NUMBER = auto()
    FLOAT = auto()
    INTEGER = auto()
    BOOLEAN = auto()
    NULL = auto()

    COMMA = auto()
    END_LINE = auto()

    # []
    OPEN_SQUARE_BRACKET = auto()
    CLOSED_SQUARE_BRACKET = auto()

    # ()
    OPEN_BRACKET = auto()
    CLOSED_BRACKET = auto()

    # {}
    OPEN_SCOPE = auto()
    CLOSED_SCOPE = auto()

    OP_ASSIGN = auto()
    OP_KEYMAP = auto()
    OP_BITWISE_OR = auto()
    OP_BITWISE_XOR = auto()
    OP_BITWISE_AND = auto()
    OP_LOGICAL = auto()
    OP_COMPARISON = auto()
    OP_BITWISE_SHIFT = auto()
    OP_ADDITIVE = auto()
    OP_MULTIPLICATIVE = auto()
    OP_POWER = auto()
    OP_BITWISE_NOT = auto()
    OP_INDEX = auto()
    OP_COALESCE = auto()

    OP_ATTRIBUTE_ACCESS = auto()
    OP_ELLIPSIS = auto()
    OP_IMPLICATION = auto()

    KEYWORD = auto()
    IDENTIFIER = auto()
    END_OF_FILE = auto()

    @staticmethod
    def identify_word(word: str):
        if word in ('if', 'else', 'elif', 'while', 'function', 'class', 'promise'):
            return Lexemes.KEYWORD
        elif word in ('and', 'or', 'not'):
            return Lexemes.OP_LOGICAL
        elif word in ('true', 'false'):
            return Lexemes.BOOLEAN
        elif word in ('null', ):
            return Lexemes.NULL
        else:
            return Lexemes.IDENTIFIER
