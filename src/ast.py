from abc import ABC, abstractmethod
from itertools import pairwise
from typing import Self, Literal

from src.exceptions import DIRuntimeSyntaxError, DITypeError, DIZeroDivisionError, DINameError, DIValueError
from src.wrappers import LiteralWrapper


class ASTRoot(ABC):

    _MIDDLE_VAR = '├──'
    _LAST_VAR = '└──'
    _EMPTY = '    '
    _GOING = '│   '

    def __init__(self, line, pos):
        self.line = line
        self.pos = pos

    @classmethod
    def print_tree(
        cls,
        tree: Self | list[Self],
        indent: str = "",
        last: bool | None = None,
    ):
        if not isinstance(tree, (ASTRoot, list)):
            return str(tree) + "\n"

        if last is not None:
            indent += (cls._EMPTY if last else cls._GOING)

        if isinstance(tree, list):

            arg_num = len(tree)
            result_string = "\n"
            for index, item in enumerate(tree):
                marker = cls._LAST_VAR if index == arg_num - 1 else cls._MIDDLE_VAR

                substr = cls.print_tree(item, indent, index == arg_num - 1)
                result_string += f"{indent}{marker}{substr}"

            return result_string

        res = tree.node_type() + '\n'

        attrs = tree.__dict__.copy()
        arg_num = len(attrs)
        for index, (arg_name, arg_value) in enumerate(attrs.items()):
            arg_name = arg_name.lstrip("_")
            marker = cls._LAST_VAR if index == arg_num - 1 else cls._MIDDLE_VAR
            substr = cls.print_tree(arg_value, indent, index == arg_num - 1)
            res += f"{indent}{marker}{arg_name}: {substr}"
        return res

    def print(self) -> str:
        return ASTRoot.print_tree(self)

    def __repr__(self):
        return self.node_type()

    def node_type(self) -> str:
        return type(self).__name__.replace("Node", "")

    @abstractmethod
    def evaluate(self, environment: dict) -> LiteralWrapper:
        pass


class ScopeNode(ASTRoot):
    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)
        self.instructions = []

    def evaluate(self, environment: dict):
        old_environment = set(environment.keys())

        last = None, None
        for instruction in self.instructions:
            last = instruction.evaluate(environment)

        redundant_variables = set(environment.keys())
        redundant_variables.difference_update(old_environment)
        for variable_to_delete in redundant_variables:
            environment.pop(variable_to_delete, None)

        return last


class IfElseNode(ASTRoot):
    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)
        self.conditions: list[ASTRoot] = []
        self.branch_scopes: list[ScopeNode] = []
        self.else_scope = None

    def add_branch(self, condition: ASTRoot | None, scope: ScopeNode):
        if condition is None:
            self.else_scope = scope
        else:
            self.conditions.append(condition)
            self.branch_scopes.append(scope)

    def evaluate(self, environment: dict) -> LiteralWrapper:
        for condition, scope in zip(self.conditions, self.branch_scopes):
            if condition.evaluate(environment):
                return scope.evaluate(environment)
        if self.else_scope is not None:
            return self.else_scope.evaluate(environment)

        return LiteralWrapper(None)


class WhileNode(ASTRoot):
    def __init__(self, line: int, pos: int, condition=None, scope=None):
        super().__init__(line, pos)
        self.condition = condition
        self.scope = scope

    def evaluate(self, environment: dict):
        result = LiteralWrapper(None)
        # (self.condition.evaluate(environment))
        while self.condition.evaluate(environment):
            result = self.scope.evaluate(environment)
        return result


class OperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator, operands=None, associativity=None):
        super().__init__(line, pos)
        self.operator = operator
        self.operands = operands or []
        self.associativity: Literal['left', 'right', 'no'] = associativity or 'left'

    def evaluate(self, environment: dict):
        if self.operator == 'or':
            for operand in self.operands:
                if operand:
                    return operand
            return self.operands[-1]
        elif self.operator == 'and':
            for operand in self.operands:
                if not operand:
                    return operand
            return self.operands[-1]
        elif self.operator == ':=':
            value = self.operands[-1].evaluate(environment)
            for identifier in reversed(self.operands[:-1]):
                if not isinstance(identifier, IdentifierNode):
                    raise DIRuntimeSyntaxError(self.line, self.pos, f"cannot assign to expression here: {identifier}")
                environment[identifier.name] = value
            return value
        elif self.operator == '**':
            value = self.operands[-1].evaluate(environment)
            for operand in reversed(self.operands[:-1]):
                value = operand.evaluate(environment) ** value
            return value
        elif self.operator == '^':
            value = self.operands[0].evaluate(environment)
            for operand in self.operands[1:]:
                value = value ^ operand.evaluate(environment)
            return value
        elif self.operator == '&':
            value = self.operands[0].evaluate(environment)
            for operand in self.operands[1:]:
                value = value & operand.evaluate(environment)
            return value
        elif self.operator == '|':
            value = self.operands[0].evaluate(environment)
            for operand in self.operands[1:]:
                value = value | operand.evaluate(environment)
            return value

        elif self.operator == '$func':
            value = self.operands[0].evaluate(environment)
            for operand in self.operands[1:]:
                if not callable(value):
                    raise DITypeError(self.line, self.pos, f'Not a function: {value}')
                value = value([o.evaluate(environment) for o in operand])
            return value

        elif self.operator == '$index':
            # TODO: implement indexation
            pass
            return LiteralWrapper(None)


class ComparisonPolyOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operators=None, operands=None):
        super().__init__(line, pos)
        self.operators = operators or []
        self.operands = operands or []
        # self.associativity: Literal['left', 'right', 'proxy-left'] = associativity or 'left'

    def evaluate(self, environment: dict):

        result = True
        for op, (lhs_, rhs_) in zip(self.operators, pairwise(self.operands)):

            lhs = lhs_.evaluate(environment)
            rhs = rhs_.evaluate(environment)

            if op == '<=':
                result = lhs <= rhs
            elif op == '>=':
                result = lhs >= rhs
            elif op == '<':
                result = lhs < rhs
            elif op == '>':
                result = lhs > rhs
            elif op == '==':
                result = lhs == rhs
            elif op == '!=':
                result = lhs != rhs

            if not result:
                return False
        return True


class LeftAssociativePolyOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operators=None, operands=None):
        super().__init__(line, pos)
        self.operators = operators or []
        self.operands = operands or []
        # self.associativity: Literal['left', 'right', 'proxy-left'] = associativity or 'left'

    def evaluate(self, environment: dict):

        lhs = self.operands[0].evaluate(environment)
        iterator = zip(self.operators, self.operands[1:])

        value = None
        for op, next_value in iterator:
            rhs = next_value.evaluate(environment)

            if op == '+':
                value = lhs + rhs
            elif op == '-':
                value = lhs - rhs
            elif op == '*':
                value = lhs * rhs
            elif op == '/':
                try:
                    value = lhs / rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} / {rhs}. Rhs is {next_value}")
            elif op == '//':
                try:
                    value = lhs // rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} // {rhs}")
            elif op == '%':
                try:
                    value = lhs % rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} % {rhs}")
            elif op == '@':
                try:
                    value = lhs @ rhs
                except TypeError as e:
                    raise DITypeError(self.line, self.pos, str(e))
                except ValueError as e:
                    raise DIValueError(self.line, self.pos, str(e))
            elif op == '<<':
                value = lhs << rhs
            elif op == '>>':
                value = lhs >> rhs
            else:
                value = None
        return value


class UnaryOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator, operand=None):
        super().__init__(line, pos)
        self.operator = operator
        self.operand = operand

    def evaluate(self, environment: dict):
        if self.operator == '-':
            return -self.operand.evaluate(environment)
        elif self.operator == '+':
            return self.operand.evaluate(environment)
        elif self.operator == '~':
            return ~self.operand.evaluate(environment)
        elif self.operator == 'not':
            return not self.operand.evaluate(environment)

        raise NotImplemented


class FunctionDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode):
        super().__init__(line, pos)
        self.params = params
        self.body = scope

    def __repr__(self):
        return self.node_type() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: dict):
        def func(params):
            environment_copy = environment.copy()

            for (param, arg) in zip(self.params, params, strict=True):
                environment_copy[param.name] = arg
            # print(environment_copy)
            return self.body.evaluate(environment_copy)
        return func


class NumberNode(ASTRoot):
    def __init__(self, line: int, pos: int, number):
        super().__init__(line, pos)
        self.number = number

    def evaluate(self, environment: dict):
        return LiteralWrapper(self.number)


class StringNode(ASTRoot):
    def __init__(self, line: int, pos: int, string):
        super().__init__(line, pos)
        self.string = string

    def evaluate(self, environment: dict):
        return LiteralWrapper(self.string)


class ListNode(ASTRoot):
    def __init__(self, line: int, pos: int, elements):
        super().__init__(line, pos)
        self.elements = elements

    def evaluate(self, environment: dict):
        return LiteralWrapper([e.evaluate(environment) for e in self.elements])


class IdentifierNode(ASTRoot):

    def __init__(self, line: int, pos: int, name):
        super().__init__(line, pos)
        self.name = name

    def __repr__(self):
        return self.node_type() + f'({self.name})'

    def evaluate(self, environment: dict):
        if self.name in environment:
            return environment[self.name]
        raise DINameError(self.line, self.pos, f"Variable {self.name} is not defined")
        # return LiteralWrapper(None)
