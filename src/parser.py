from .ast import (
    ASTRoot,
    IfElseNode, WhileNode, OperatorNode, ComparisonNode, BooleanNode, NullNode,
    UnaryOperatorNode, FunctionDeclarationNode, EllipsisOperatorNode,
    NumberNode, ListNode, IdentifierNode, StringNode, ClassDeclarationNode, AssignmentNode,
    ScopeNode, FunctionCallNode, IndexationNode, AttributeCallNode
)
from .exceptions import DIStaticSyntaxError
from .lexemes import Lexemes
from .lexer import Lexer

from typing import NoReturn


class Parser:

    def __init__(self, lexer: Lexer) -> None:
        self.tokens = [lex for lex in lexer]
        self.i = 0

    def get_prev(self) -> None:
        self.i -= 1

    def get_next(self) -> None:
        self.i += 1

    def was_previous_consumable(self, token_type: Lexemes, token_value: str | None = None) -> bool:
        if self.prev_token is None:
            return False

        if token_value is None:
            return self.prev_token[0] == token_type

        return self.prev_token[0:2] == (token_type, token_value)


    def is_consumable(self, token_type: Lexemes, token_value: str | None = None) -> bool:
        if self.curr_token is None:
            return False

        if token_value is None:
            return self.curr_token[0] == token_type

        return self.curr_token[0:2] == (token_type, token_value)

    def consume(self, token_type: Lexemes) -> str | int | float:
        if self.curr_token is None or self.curr_token[0] != token_type:
            self.error(f"Expected token mismatch: expected {token_type.name}, found {self.curr_token[0].name}")
        val = self.curr_token[1]
        self.get_next()
        return val

    def error(self, reason) -> NoReturn:
        pt = str(self.prev_token[1]) if self.prev_token else ''
        ct = str(self.curr_token[1]) if self.curr_token else ''

        _, _, line, char = self.curr_token
        raise DIStaticSyntaxError(
            self.line, self.pos,
            f"\nParsing error: '{pt}' '{ct}'\n" +
            f" " * (len(pt) + 18) + " " + "^" * len(ct) +
            f"\nInvalid token found in line {line}, character {char}\n" +
            reason
        )

    @property
    def curr_token(self) -> None | tuple[Lexemes, str | int | float, int, int]:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    @property
    def prev_token(self) -> None | tuple[Lexemes, str | int | float, int, int]:
        return self.tokens[self.i - 1] if 1 < self.i <= len(self.tokens) else None

    @property
    def line(self):
        return self.prev_token[2] if self.prev_token else 0

    @property
    def pos(self):
        return self.prev_token[3] if self.prev_token else -1

    def skip_end_lines(self) -> None:
        while self.is_consumable(Lexemes.END_LINE):
            self.get_next()

    def revert_last_end_line(self):
        if self.was_previous_consumable(Lexemes.END_LINE):
            self.get_prev()

    def parse_program(self) -> ScopeNode:
        scope_node = ScopeNode(0, 0)

        while not self.is_consumable(Lexemes.END_OF_FILE):
            scope_node.instructions.append(self.parse_expression())

        self.consume(Lexemes.END_OF_FILE)

        return scope_node

    def parse_expression(self) -> ASTRoot:
        while self.is_consumable(Lexemes.END_LINE):
            self.consume(Lexemes.END_LINE)

        value: ASTRoot = self.parse_assignment()
        self.skip_end_lines()
        return value

    def parse_assignment(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_coalesce()
        if self.is_consumable(Lexemes.OP_ASSIGN):
            self.consume(Lexemes.OP_ASSIGN)
            return AssignmentNode(
                lhs=lhs, rhs=self.parse_assignment(),
                line=self.line, pos=self.pos
            )
        return lhs

    def parse_coalesce(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_logical_or()
        if self.is_consumable(Lexemes.OP_COALESCE):
            self.consume(Lexemes.OP_COALESCE)
            return OperatorNode(self.line, self.pos, '?', lhs, self.parse_coalesce())
        return lhs

    def parse_logical_or(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_logical_and()
        if self.is_consumable(Lexemes.OP_LOGICAL, 'or'):
            self.consume(Lexemes.OP_LOGICAL)
            return OperatorNode(self.line, self.pos, 'or', lhs, self.parse_logical_or())
        return lhs

    def parse_logical_and(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_logical_not()
        if self.is_consumable(Lexemes.OP_LOGICAL, 'and'):
            self.consume(Lexemes.OP_LOGICAL)
            return OperatorNode(self.line, self.pos, 'and', lhs, self.parse_logical_and())
        return lhs

    def parse_logical_not(self) -> UnaryOperatorNode | ASTRoot:
        if self.is_consumable(Lexemes.OP_LOGICAL, 'not'):
            self.consume(Lexemes.OP_LOGICAL)
            return UnaryOperatorNode(self.line, self.pos, 'not', self.parse_comparison())
        else:
            return self.parse_comparison()

    def parse_comparison(self) -> ComparisonNode | ASTRoot:
        lhs = self.parse_bitwise_or()
        rhs = None
        if self.is_consumable(Lexemes.OP_COMPARISON):
            op = self.consume(Lexemes.OP_COMPARISON)
            rhs = self.parse_bitwise_or()
            lhs = ComparisonNode(self.line, self.pos, op, lhs, rhs)
        while self.is_consumable(Lexemes.OP_COMPARISON):
            op = self.consume(Lexemes.OP_COMPARISON)
            new_rhs = self.parse_bitwise_or()
            lhs = OperatorNode(
                self.line, self.pos, 'and', lhs, ComparisonNode(self.line, self.pos, op, rhs, new_rhs)
            )
            rhs = new_rhs
        return lhs

    def parse_bitwise_or(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_bitwise_xor()
        while self.is_consumable(Lexemes.OP_BITWISE_OR):
            self.consume(Lexemes.OP_BITWISE_OR)
            lhs = OperatorNode(self.line, self.pos, '|', lhs, self.parse_bitwise_xor())
        return lhs

    def parse_bitwise_xor(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_bitwise_and()
        while self.is_consumable(Lexemes.OP_BITWISE_XOR):
            self.consume(Lexemes.OP_BITWISE_XOR)
            lhs = OperatorNode(self.line, self.pos, '^', lhs, self.parse_bitwise_and())
        return lhs

    def parse_bitwise_and(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_bitwise_shifts()
        while self.is_consumable(Lexemes.OP_BITWISE_AND):
            self.consume(Lexemes.OP_BITWISE_AND)
            lhs = OperatorNode(self.line, self.pos, '&', lhs, self.parse_bitwise_shifts())
        return lhs

    def parse_bitwise_shifts(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_additive()
        while self.is_consumable(Lexemes.OP_BITWISE_SHIFT):
            op = self.consume(Lexemes.OP_BITWISE_SHIFT)
            lhs = OperatorNode(self.line, self.pos, op, lhs, self.parse_additive())
        return lhs

    def parse_additive(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_multiplicative()
        while self.is_consumable(Lexemes.OP_ADDITIVE):
            op = self.consume(Lexemes.OP_ADDITIVE)
            lhs = OperatorNode(self.line, self.pos, op, lhs, self.parse_multiplicative())
        return lhs

    def parse_multiplicative(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_power()
        while self.is_consumable(Lexemes.OP_MULTIPLICATIVE):
            op = self.consume(Lexemes.OP_MULTIPLICATIVE)
            lhs = OperatorNode(self.line, self.pos, op, lhs, self.parse_power())
        return lhs

    def parse_power(self) -> OperatorNode | ASTRoot:
        lhs = self.parse_unary()
        if self.is_consumable(Lexemes.OP_POWER):
            self.consume(Lexemes.OP_POWER)
            return OperatorNode(self.line, self.pos, '**', lhs, self.parse_power())
        return lhs

    def parse_unary(self) -> UnaryOperatorNode | ASTRoot:
        if self.is_consumable(Lexemes.OP_ADDITIVE):
            op = self.consume(Lexemes.OP_ADDITIVE)
            return UnaryOperatorNode(self.line, self.pos, op, self.parse_function_call())
        elif self.is_consumable(Lexemes.OP_INDEX):
            op = self.consume(Lexemes.OP_INDEX)
            return UnaryOperatorNode(self.line, self.pos, op, self.parse_function_call())
        elif self.is_consumable(Lexemes.OP_ELLIPSIS):
            self.consume(Lexemes.OP_ELLIPSIS)
            return EllipsisOperatorNode(self.line, self.pos, self.parse_function_call())
        else:
            return self.parse_function_call()

    def _parse_comma_separated_args(self, opening: Lexemes, closing: Lexemes) -> list[ASTRoot]:
        res = []
        self.consume(opening)
        while not self.is_consumable(closing):
            res.append(self.parse_expression())
            if self.is_consumable(closing):
                break

            self.consume(Lexemes.COMMA)
            while self.is_consumable(Lexemes.END_LINE):
                self.consume(Lexemes.END_LINE)
        self.consume(closing)
        return res

    def parse_function_call(self) -> FunctionCallNode | ASTRoot:
        lhs = self.parse_indexation()
        while self.is_consumable(Lexemes.OPEN_BRACKET):
            lhs = FunctionCallNode(
                self.line, self.pos, lhs, self._parse_comma_separated_args(Lexemes.OPEN_BRACKET, Lexemes.CLOSED_BRACKET)
            )
        return lhs

    def parse_indexation(self) -> IndexationNode | ASTRoot:
        lhs = self.parse_member_access()
        while self.is_consumable(Lexemes.OPEN_SQUARE_BRACKET):
            lhs = IndexationNode(
                self.line, self.pos, lhs,
                self._parse_comma_separated_args(Lexemes.OPEN_SQUARE_BRACKET, Lexemes.CLOSED_SQUARE_BRACKET))
        return lhs

    def parse_member_access(self) -> AttributeCallNode | ASTRoot:
        lhs = self.parse_primary()
        while self.is_consumable(Lexemes.OP_ATTRIBUTE_ACCESS):
            self.consume(Lexemes.OP_ATTRIBUTE_ACCESS)
            lhs = AttributeCallNode(self.line, self.pos, lhs, self.parse_identifier())
        return lhs

    def parse_primary(self) -> ASTRoot:

        if self.is_consumable(Lexemes.INTEGER):
            # note: kwargs order is important
            sub_result = NumberNode(
                number=self.consume(Lexemes.INTEGER),
                line=self.line, pos=self.pos
            )

        elif self.is_consumable(Lexemes.FLOAT):
            # note: kwargs order is important
            sub_result = NumberNode(
                number=self.consume(Lexemes.FLOAT),
                line=self.line, pos=self.pos
            )

        elif self.is_consumable(Lexemes.STRING):
            # note: kwargs order is important
            sub_result = StringNode(
                string=self.consume(Lexemes.STRING),
                line=self.line, pos=self.pos
            )

        elif self.is_consumable(Lexemes.BOOLEAN):
            # note: kwargs order is important
            sub_result = BooleanNode(
                value=self.consume(Lexemes.NUMBER),
                line=self.line, pos=self.pos
            )

        elif self.is_consumable(Lexemes.NULL):
            self.consume(Lexemes.NULL)
            sub_result = NullNode(self.line, self.pos)

        elif self.is_consumable(Lexemes.OPEN_SQUARE_BRACKET):
            sub_result = self.parse_list()

        elif self.is_consumable(Lexemes.OPEN_BRACKET):
            self.consume(Lexemes.OPEN_BRACKET)
            sub_result = self.parse_expression()
            self.consume(Lexemes.CLOSED_BRACKET)

        elif self.is_consumable(Lexemes.IDENTIFIER):
            sub_result = self.parse_identifier()

        elif self.is_consumable(Lexemes.OPEN_SCOPE):
            sub_result = self.parse_scope()

        elif self.is_consumable(Lexemes.KEYWORD, 'if'):
            sub_result = self.parse_if()

        elif self.is_consumable(Lexemes.KEYWORD, 'while'):
            sub_result = self.parse_while()

        elif self.is_consumable(Lexemes.KEYWORD, 'function'):
            sub_result = self.parse_function()

        elif self.is_consumable(Lexemes.KEYWORD, 'class'):
            sub_result = self.parse_class()

        else:
            self.error(f"Invalid terminal type: {self.curr_token[0].name}")

        return sub_result

    def parse_list(self) -> ListNode:

        res = []

        self.consume(Lexemes.OPEN_SQUARE_BRACKET)
        line, pos = self.line, self.pos
        while not self.is_consumable(Lexemes.CLOSED_SQUARE_BRACKET):
            res.append(self.parse_expression())
            if self.is_consumable(Lexemes.CLOSED_SQUARE_BRACKET):
                break

            _ = self.consume(Lexemes.COMMA)
            while self.is_consumable(Lexemes.END_LINE):
                self.consume(Lexemes.END_LINE)
        self.consume(Lexemes.CLOSED_SQUARE_BRACKET)
        return ListNode(line, pos, res)

    def parse_scope(self) -> ScopeNode:

        if not self.is_consumable(Lexemes.OPEN_SCOPE):
            instruction = self.parse_expression()
            scope_node = ScopeNode(instruction.line, instruction.pos)
            scope_node.instructions.append(instruction)
            return scope_node

        self.consume(Lexemes.OPEN_SCOPE)
        scope_node = ScopeNode(self.line, self.pos)
        while not self.is_consumable(Lexemes.CLOSED_SCOPE):
            scope_node.instructions.append(self.parse_expression())
        self.consume(Lexemes.CLOSED_SCOPE)

        return scope_node

    def parse_if(self) -> IfElseNode:

        _ = self.consume(Lexemes.KEYWORD)

        if_else_node = IfElseNode(self.line, self.pos)
        if_else_node.add_branch(self.parse_condition(), self.parse_scope())
        self.skip_end_lines()

        while self.is_consumable(Lexemes.KEYWORD, 'elif'):
            _ = self.consume(Lexemes.KEYWORD)
            if_else_node.add_branch(self.parse_condition(), self.parse_scope())
            self.skip_end_lines()

        if self.is_consumable(Lexemes.KEYWORD, 'else'):
            self.consume(Lexemes.KEYWORD)
            if_else_node.add_branch(None, self.parse_scope())
            self.skip_end_lines()

        self.revert_last_end_line()
        return if_else_node

    def parse_while(self) -> WhileNode:
        self.consume(Lexemes.KEYWORD)
        return WhileNode(self.line, self.pos, self.parse_condition(), self.parse_scope())

    def parse_class(self) -> ClassDeclarationNode:
        params = []
        self.consume(Lexemes.KEYWORD)
        self.consume(Lexemes.OPEN_BRACKET)
        while not self.is_consumable(Lexemes.CLOSED_BRACKET):
            params.append(self.parse_identifier())
            if self.is_consumable(Lexemes.CLOSED_BRACKET):
                break

            _ = self.consume(Lexemes.COMMA)
            while self.is_consumable(Lexemes.END_LINE):
                self.consume(Lexemes.END_LINE)
        self.consume(Lexemes.CLOSED_BRACKET)
        return ClassDeclarationNode(self.line, self.pos, params, self.parse_scope())

    def parse_function(self) -> FunctionDeclarationNode:

        _ = self.consume(Lexemes.KEYWORD)
        line, pos = self.line, self.pos
        params = []

        self.consume(Lexemes.OPEN_BRACKET)
        while not self.is_consumable(Lexemes.CLOSED_BRACKET):
            if self.is_consumable(Lexemes.IDENTIFIER):
                params.append(self.parse_identifier())
            elif self.is_consumable(Lexemes.OP_ELLIPSIS):
                self.consume(Lexemes.OP_ELLIPSIS)
                params.append(
                    EllipsisOperatorNode(
                        self.line, self.pos,
                        self.parse_identifier()
                    )
                )
            else:
                self.error("Unexpected token in function declaration params")
            if self.is_consumable(Lexemes.CLOSED_BRACKET):
                break

            _ = self.consume(Lexemes.COMMA)
            while self.is_consumable(Lexemes.END_LINE):
                self.consume(Lexemes.END_LINE)
        self.consume(Lexemes.CLOSED_BRACKET)
        return FunctionDeclarationNode(line, pos, params, self.parse_scope())

    def parse_condition(self) -> ASTRoot:
        self.consume(Lexemes.OPEN_BRACKET)
        result: ASTRoot = self.parse_logical_or()
        self.consume(Lexemes.CLOSED_BRACKET)
        return result

    def parse_identifier(self):
        return IdentifierNode(
            name=self.consume(Lexemes.IDENTIFIER),
            line=self.line, pos=self.pos
        )


