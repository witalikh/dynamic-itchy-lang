from .ast import (
    ASTRoot,
    IfElseNode, WhileNode, OperatorNode, ComparisonNode, BooleanNode, NullNode,
    LeftPolyOperatorNode, UnaryOperatorNode, FunctionDeclarationNode, EllipsisOperatorNode,
    NumberNode, ListNode, IdentifierNode, StringNode, ClassDeclarationNode, AssignmentNode,
    ScopeNode
)
from .exceptions import DIStaticSyntaxError
from .lexemes import Lexemes
from .lexer import Lexer

from typing import NoReturn


class Parser:

    def __init__(self, lexer: Lexer) -> None:
        self.tokens = [lex for lex in lexer]
        self.i = 0

    def get_next(self) -> None:
        self.i += 1

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
        while self.is_consumable(Lexemes.END_LINE):
            self.consume(Lexemes.END_LINE)
        return value

    # def parse_comma(self) -> ASTRoot:
    #     expr = self.parse_assignment()
    #     if not self.is_consumable(Lexemes.COMMA):
    #         return expr
    #
    #     tup = [expr]
    #     while self.is_consumable(Lexemes.COMMA):
    #         self.consume(Lexemes.COMMA)
    #         tup.append(self.parse_assignment())
    #     return ListNode(self.line, self.pos, tup)

    def parse_assignment(self) -> OperatorNode | ASTRoot:

        operand = self.parse_logical_or()
        if not self.is_consumable(Lexemes.OP_ASSIGN):
            return operand

        operands = [operand]
        lasts = []

        while self.is_consumable(Lexemes.OP_ASSIGN):
            lasts.append(self.consume(Lexemes.OP_ASSIGN) == '=:')
            operands.append(self.parse_logical_or())

        return AssignmentNode(operand.line, operand.pos, operands, lasts)

    def parse_logical_or(self) -> OperatorNode | ASTRoot:

        left_expr = self.parse_logical_and()
        if not self.is_consumable(Lexemes.OP_LOGICAL, 'or'):
            return left_expr

        operands = [left_expr]
        while self.is_consumable(Lexemes.OP_LOGICAL, 'or'):
            self.consume(Lexemes.OP_LOGICAL)
            operands.append(self.parse_logical_and())
        return OperatorNode(left_expr.line, left_expr.pos, 'or', operands)

    def parse_logical_and(self) -> OperatorNode | ASTRoot:
        left_expr = self.parse_logical_not()
        if not self.is_consumable(Lexemes.OP_LOGICAL, 'and'):
            return left_expr

        operands = [left_expr]
        while self.is_consumable(Lexemes.OP_LOGICAL, 'and'):
            self.consume(Lexemes.OP_LOGICAL)
            operands.append(self.parse_logical_not())

        return OperatorNode(left_expr.line, left_expr.pos, 'and', operands)

    def parse_logical_not(self) -> UnaryOperatorNode | ASTRoot:
        if self.is_consumable(Lexemes.OP_LOGICAL, 'not'):
            self.consume(Lexemes.OP_LOGICAL)
            return UnaryOperatorNode(self.line, self.pos, 'not', self.parse_comparison())

        else:
            return self.parse_comparison()

    def parse_comparison(self) -> LeftPolyOperatorNode | ASTRoot:

        operand = self.parse_bitwise_or()
        if not self.is_consumable(Lexemes.OP_COMPARISON):
            return operand

        operands = [operand]
        operators = []

        while self.is_consumable(Lexemes.OP_COMPARISON):
            operators.append(self.consume(Lexemes.OP_COMPARISON))
            operands.append(self.parse_bitwise_or())

        return ComparisonNode(operand.line, operand.pos, operators, operands)

    def parse_bitwise_or(self) -> OperatorNode | ASTRoot:

        operand = self.parse_bitwise_xor()
        if not self.is_consumable(Lexemes.OP_BITWISE_OR):
            return operand

        operands = [operand]

        while self.is_consumable(Lexemes.OP_BITWISE_OR):
            self.consume(Lexemes.OP_BITWISE_OR)
            operands.append(self.parse_bitwise_xor())

        return OperatorNode(operand.line, operand.pos, '|', operands)

    def parse_bitwise_xor(self) -> OperatorNode | ASTRoot:

        operand = self.parse_bitwise_and()
        if not self.is_consumable(Lexemes.OP_BITWISE_XOR):
            return operand

        operands = [operand]

        while self.is_consumable(Lexemes.OP_BITWISE_XOR):
            self.consume(Lexemes.OP_BITWISE_XOR)
            operands.append(self.parse_bitwise_and())

        return OperatorNode(operand.line, operand.pos, '^', operands)

    def parse_bitwise_and(self) -> OperatorNode | ASTRoot:

        operand = self.parse_bitwise_shifts()
        if not self.is_consumable(Lexemes.OP_BITWISE_AND):
            return operand

        operands = [operand]

        while self.is_consumable(Lexemes.OP_BITWISE_AND):
            self.consume(Lexemes.OP_BITWISE_AND)
            operands.append(self.parse_bitwise_shifts())

        return OperatorNode(operand.line, operand.pos, '|', operands)

    def parse_bitwise_shifts(self) -> LeftPolyOperatorNode | ASTRoot:

        operand = self.parse_additive()
        if not self.is_consumable(Lexemes.OP_BITWISE_SHIFT):
            return operand

        operands = [operand]
        operators = []

        while self.is_consumable(Lexemes.OP_BITWISE_SHIFT):
            operators.append(self.consume(Lexemes.OP_BITWISE_SHIFT))
            operands.append(self.parse_additive())

        return LeftPolyOperatorNode(operand.line, operand.pos, operators, operands)

    def parse_additive(self) -> LeftPolyOperatorNode | ASTRoot:

        operand = self.parse_multiplicative()
        if not self.is_consumable(Lexemes.OP_ADDITIVE):
            return operand

        operands = [operand]
        operators = []

        while self.is_consumable(Lexemes.OP_ADDITIVE):
            operators.append(self.consume(Lexemes.OP_ADDITIVE))
            operands.append(self.parse_multiplicative())

        return LeftPolyOperatorNode(operand.line, operand.pos, operators, operands)

    def parse_multiplicative(self) -> LeftPolyOperatorNode | ASTRoot:

        operand = self.parse_power()
        if not self.is_consumable(Lexemes.OP_MULTIPLICATIVE):
            return operand

        operands = [operand]
        operators = []

        while self.is_consumable(Lexemes.OP_MULTIPLICATIVE):
            operators.append(self.consume(Lexemes.OP_MULTIPLICATIVE))
            operands.append(self.parse_power())

        return LeftPolyOperatorNode(operand.line, operand.pos, operators, operands)

    def parse_power(self) -> OperatorNode | ASTRoot:
        operand = self.parse_unary()
        if not self.is_consumable(Lexemes.OP_POWER):
            return operand

        operands = [operand]

        while self.is_consumable(Lexemes.OP_POWER):
            _ = self.consume(Lexemes.OP_POWER)
            operands.append(self.parse_unary())

        return OperatorNode(operand.line, operand.pos, '**', operands)

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

    def parse_function_call(self) -> OperatorNode | ASTRoot:
        operand = self.parse_indexation()
        if not self.is_consumable(Lexemes.OPEN_BRACKET):
            return operand

        chain_of_args = [operand]
        while self.is_consumable(Lexemes.OPEN_BRACKET):
            chain_of_args.append(self._parse_comma_separated_args(Lexemes.OPEN_BRACKET, Lexemes.CLOSED_BRACKET))

        return OperatorNode(operand.line, operand.pos, '$func', chain_of_args)

    def parse_indexation(self) -> OperatorNode | ASTRoot:

        operand = self.parse_member_access()
        if not self.is_consumable(Lexemes.OPEN_SQUARE_BRACKET):
            return operand

        chain_of_args = [operand]

        while self.is_consumable(Lexemes.OPEN_SQUARE_BRACKET):
            chain_of_args.append(
                self._parse_comma_separated_args(Lexemes.OPEN_SQUARE_BRACKET, Lexemes.CLOSED_SQUARE_BRACKET)
            )

        return OperatorNode(operand.line, operand.pos, '$index', chain_of_args)

    def parse_member_access(self) -> OperatorNode | ASTRoot:

        operand = self.parse_primary()
        if not self.is_consumable(Lexemes.OP_ATTRIBUTE_ACCESS):
            return operand

        chain_of_args = [operand]

        line, pos = None, None
        while self.is_consumable(Lexemes.OP_ATTRIBUTE_ACCESS):
            self.consume(Lexemes.OP_ATTRIBUTE_ACCESS)
            line, pos = self.line, self.pos

            member = IdentifierNode(
                name=self.consume(Lexemes.IDENTIFIER),
                line=self.line, pos=self.pos
            )
            chain_of_args.append(member)

        return OperatorNode(line, pos, '$attr', chain_of_args)

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
            # note: kwargs order is important
            sub_result = IdentifierNode(
                name=self.consume(Lexemes.IDENTIFIER),
                line=self.line, pos=self.pos
            )

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

        while self.is_consumable(Lexemes.KEYWORD, 'elif'):
            _ = self.consume(Lexemes.KEYWORD)
            if_else_node.add_branch(self.parse_condition(), self.parse_scope())

        if self.is_consumable(Lexemes.KEYWORD, 'else'):
            self.consume(Lexemes.KEYWORD)
            if_else_node.add_branch(None, self.parse_scope())

        return if_else_node

    def parse_while(self) -> WhileNode:
        self.consume(Lexemes.KEYWORD)
        return WhileNode(self.line, self.pos, self.parse_condition(), self.parse_scope())

    # def parse_promise(self) -> WhileNode:
    #     self.consume(Lexemes.KEYWORD)
    #     return WhileNode(self.line, self.pos, self.parse_condition(), self.parse_scope())

    def parse_class(self) -> ClassDeclarationNode:
        """

        func_1(a, b) := ...
        func_2(a, b, c) := ...

        func = func_1 or func_2
        func(a, b) <=> func_

        person := class (_name, _age, _status) {
            name := _name;
            age := _age;
            status := _status;

            get_year_of_birth := function() 2024 - age;
        }

        :return:
        """

        params = []
        self.consume(Lexemes.KEYWORD)
        self.consume(Lexemes.OPEN_BRACKET)
        while not self.is_consumable(Lexemes.CLOSED_BRACKET):
            params.append(
                IdentifierNode(
                    name=self.consume(Lexemes.IDENTIFIER),
                    line=self.line, pos=self.pos  # Intentional code design: firstly consume, then get location
                )
            )
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
            params.append(
                IdentifierNode(
                    name=self.consume(Lexemes.IDENTIFIER),
                    line=self.line, pos=self.pos  # Intentional code design: firstly consume, then get location
                )
            )
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
