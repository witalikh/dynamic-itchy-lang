"""
Lexical analysis of source code
"""

from .lexemes import Lexemes
from .exceptions import DIStaticSyntaxError
from drafts.aliases import Result


from typing import NoReturn, Tuple, Self


class Lexer:

    err_scan = 'Unrecognized symbol: '

    def __init__(self, text: str) -> None:
        self.text: str = text
        self.i = 0

        self.line = 0
        self.char = 0

        self.break_line = 0

    def error(self) -> NoReturn:
        raise DIStaticSyntaxError(
            self.line, self.char,
            ''.join([self.err_scan, self.text[:self.i], "  \'", self.text[self.i], "\'"])
        )

    @property
    def prev_char(self) -> str:
        return self.text[self.i - 1] if 1 <= self.i < len(self.text) else None

    @property
    def curr_char(self) -> str:
        return self.text[self.i] if self.i < len(self.text) else None

    @property
    def next_char(self) -> str:
        return self.text[self.i + 1] if self.i < len(self.text) - 1 else None

    def pass_forward(self, step) -> None:
        """
        Go to next symbol, changing line and char position numbers
        when it's needed.
        :param step: Symbols to fast-forward
        """
        self.i += step

        if self.break_line:
            self.line += 1
            self.char = 0
        else:
            self.char += 1

        self.break_line = self.curr_char == '\n'

    def skip_comments_and_whitespace(self) -> None:
        """
        Ignore all redundant whitespace, newline characters and comments
        as much as possible
        """
        while self.curr_char:
            # skip multiline comments
            if self.curr_char == '\\' and self.next_char == '*':

                while self.curr_char != '*' or self.next_char != '\\':
                    self.pass_forward(1)
                else:
                    self.pass_forward(2)

            # skip inline comments
            elif self.curr_char == '#':

                self.pass_forward(1)
                while self.curr_char and self.curr_char != '\n':
                    self.pass_forward(1)
                else:
                    self.pass_forward(1)

            # skip whitespace
            elif self.curr_char == ' ':
                while self.curr_char == ' ':
                    self.pass_forward(1)

            else:
                break

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Tuple[Lexemes, Result, int, int] | None:

        self.skip_comments_and_whitespace()

        # reached last symbol in file or string, '\0' or '\n'
        if self.i == len(self.text):
            self.pass_forward(1)
            return Lexemes.END_OF_FILE, None, self.line, self.char

        # end of code
        if self.i > len(self.text):
            raise StopIteration

        # self.skip_comments_and_whitespace()

        # single symbol tokens
        if self.curr_char == '(':
            token = (Lexemes.OPEN_BRACKET, '(')
            self.pass_forward(1)

        elif self.curr_char == ')':
            token = (Lexemes.CLOSED_BRACKET, ')')
            self.pass_forward(1)

        elif self.curr_char == '[':
            token = (Lexemes.OPEN_SQUARE_BRACKET, '[')
            self.pass_forward(1)

        elif self.curr_char == ']':
            token = (Lexemes.CLOSED_SQUARE_BRACKET, ']')
            self.pass_forward(1)

        elif self.curr_char == '{':
            token = (Lexemes.OPEN_SCOPE, '{')
            self.pass_forward(1)

        elif self.curr_char == '}':
            token = (Lexemes.CLOSED_SCOPE, '}')
            self.pass_forward(1)

        elif self.curr_char == ',':
            token = (Lexemes.COMMA, ',')
            self.pass_forward(1)

        elif self.curr_char in '\n;':
            token = (Lexemes.END_LINE, ';')
            self.pass_forward(1)

        # numerical literals
        elif self.curr_char.isdigit():
            token = self.lex_number()

        # operators
        elif self.curr_char in ':+-*/%=<>!@#.?':
            token = self.lex_operator()

        # keywords and identifiers
        elif self.curr_char.isalpha() or self.curr_char == '_':
            token = self.lex_word()

        elif self.curr_char == "\"":
            token = self.lex_string()

        else:
            self.error()

        if token is None:
            self.error()

        pos = (self.line, self.char)
        return *token, *pos

    def lex_number(self) -> Tuple[Lexemes, Result] | NoReturn:

        right_pos = self.i

        base = 10
        allow_float = True

        first_dot_met = False

        while right_pos < len(self.text):

            # '0' in the beginning might denote different base
            # for integer
            # as well as some float number. Or just zero ;)
            if right_pos == self.i and self.text[right_pos] == '0':
                if self.text[right_pos + 1] == 'b':
                    base = 2
                    allow_float = False
                    right_pos += 2

                elif self.text[right_pos + 1] == 'x':
                    base = 16
                    allow_float = False
                    right_pos += 2
                elif self.text[right_pos + 1] == 'o':
                    base = 8
                    allow_float = False
                    right_pos += 2
                elif self.text[right_pos + 1] == 'q':
                    base = 4
                    allow_float = False
                    right_pos += 2

            # accept float part notation if possible
            # (when base is 10)
            if allow_float:

                # accept all decimals and first dot
                if self.text[right_pos].isdigit():
                    right_pos += 1

                elif not first_dot_met and self.text[right_pos] == '.':
                    first_dot_met = True
                    right_pos += 1

                elif self.text[right_pos] in 'eE':
                    if not (self.text[right_pos + 1].isdigit() or self.text[right_pos + 1] in '+-'):
                        break

                    right_pos += 1
                    if self.text[right_pos] in '+-':
                        right_pos += 1
                else:
                    break

            # handle integers in different bases
            else:
                if base == 10 and self.text[right_pos].isdigit():
                    right_pos += 1
                elif base == 8 and self.text[right_pos] in '01234567':
                    right_pos += 1
                elif base == 2 and self.text[right_pos] in '01':
                    right_pos += 1
                elif base == 4 and self.text[right_pos] in '0123':
                    right_pos += 1
                elif base == 16 and (self.text[right_pos].isdigit() or self.text[right_pos] in 'ABCDEF'):
                    right_pos += 1
                else:
                    break

        # extract whole numeric
        num = self.text[self.i:right_pos]

        # shift pointer to it's sentinel
        self.pass_forward(right_pos - self.i)

        # convert into standard numeric
        try:
            if not first_dot_met:
                if base == 4:
                    num = num[2:]
                num = int(num, base)
                return Lexemes.INTEGER, num
            else:
                num = float(num)
                return Lexemes.FLOAT, num

        except ValueError:
            self.error()

    def lex_operator(self) -> Tuple[Lexemes, str]:

        # :+-*/%=<>!@#.?

        # '+', '-'
        if self.curr_char in '+-':
            char = self.curr_char
            self.pass_forward(1)
            return Lexemes.OP_ADDITIVE, char

        # '&'
        elif self.curr_char == '&':
            char = self.curr_char
            self.pass_forward(1)
            return Lexemes.OP_BITWISE_AND, char

        # '^'
        elif self.curr_char == '^':
            char = self.curr_char
            self.pass_forward(1)
            return Lexemes.OP_BITWISE_XOR, char

        # '|'
        elif self.curr_char == '|':
            char = self.curr_char
            self.pass_forward(1)
            return Lexemes.OP_BITWISE_OR, char

        # '~'
        elif self.curr_char == '~':
            char = self.curr_char
            self.pass_forward(1)
            return Lexemes.OP_BITWISE_NOT, char

        # '*', '**'
        elif self.curr_char == '*':
            if self.next_char == '*':
                self.pass_forward(2)
                return Lexemes.OP_POWER, '**'
            else:
                self.pass_forward(1)
                return Lexemes.OP_MULTIPLICATIVE, '*'

        # '/', '//'
        elif self.curr_char == '/':
            if self.next_char == '/':
                self.pass_forward(2)
                return Lexemes.OP_MULTIPLICATIVE, "//"
            else:
                self.pass_forward(1)
                return Lexemes.OP_MULTIPLICATIVE, "/"

        # '%'
        elif self.curr_char == '%':
            self.pass_forward(1)
            return Lexemes.OP_MULTIPLICATIVE, '%'

        # '@'
        elif self.curr_char == '@':
            self.pass_forward(1)
            return Lexemes.OP_MULTIPLICATIVE, '@'

        # '>=' '<=' '>' '<' '>>' '<<'
        elif self.curr_char in "<>":
            char = self.curr_char
            if self.next_char == '=':
                self.pass_forward(2)
                value = char + '='
                return Lexemes.OP_COMPARISON, value
            elif self.next_char == self.curr_char:
                self.pass_forward(2)
                value = char + self.next_char
                return Lexemes.OP_BITWISE_SHIFT, value
            else:
                self.pass_forward(1)
                value = char
                return Lexemes.OP_COMPARISON, value

        # '!='
        elif self.curr_char == "!" and self.next_char == "=":
            self.pass_forward(2)
            return Lexemes.OP_COMPARISON, '!='

        # '=='
        elif self.curr_char == self.next_char == "=":
            self.pass_forward(2)
            return Lexemes.OP_COMPARISON, '=='

        # ':='
        elif self.curr_char == ":" and self.next_char == "=":
            self.pass_forward(2)
            return Lexemes.OP_ASSIGN, ':='

        elif self.curr_char == "=" and self.next_char == ">":
            self.pass_forward(2)
            return Lexemes.OP_IMPLICATION, "=>"

        elif self.curr_char == ":":
            self.pass_forward(1)
            return Lexemes.OP_KEYMAP, ':'

        elif self.curr_char == "?":
            self.pass_forward(1)
            return Lexemes.OP_COALESCE, '?'

        elif self.curr_char == ".":
            self.pass_forward(1)
            if self.curr_char == self.next_char == ".":
                self.pass_forward(2)
                return Lexemes.OP_ELLIPSIS, "..."
            else:
                return Lexemes.OP_ATTRIBUTE_ACCESS, "."

        else:
            self.error()

    def lex_word(self) -> Tuple[Lexemes, str]:

        k = self.i
        while k < len(self.text) and any((
            self.text[k].isalpha(), self.text[k] == '_', k != self.i and self.text[k].isdigit(),
        )):
            k += 1
        name = self.text[self.i:k]

        self.pass_forward(k - self.i)
        return Lexemes.identify_word(name), name

    def lex_string(self) -> Tuple[Lexemes, str]:

        k = self.i
        # skip first quote
        k += 1

        # escaped backslash
        escaped_backslash = False

        while k < len(self.text) and (escaped_backslash or self.text[k] != '"') and self.text[k] != '\n':
            if self.text[k] == '\\':
                escaped_backslash = not escaped_backslash
            if escaped_backslash and self.text[k] != '\\':
                escaped_backslash = False
            k += 1
        else:
            if self.text[k] != '"' or escaped_backslash:
                self.error()
            # skip last quotation mark
            k += 1
        name = self.text[self.i:k]

        self.pass_forward(k - self.i)
        return Lexemes.STRING, name
