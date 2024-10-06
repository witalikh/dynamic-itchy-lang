from abc import ABC, abstractmethod
from itertools import pairwise, chain
from typing import Self, Literal

from src.exceptions import (
    DIRuntimeSyntaxError, DITypeError, DIZeroDivisionError,
    DINameError, DIValueError, DIIndexError
)
from src.wrappers import NumericWrapper, ListWrapper, StringWrapper, DictWrapper, FunctionWrapper


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
    def evaluate(self, environment: dict) -> NumericWrapper:
        pass


class ScopeNode(ASTRoot):
    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)
        self.instructions = []

    def evaluate(self, environment: dict, flush_variables: bool = True):
        old_environment = set(environment.keys())

        last = NumericWrapper(None)
        for instruction in self.instructions:
            last = instruction.evaluate(environment)

        if flush_variables:
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

    def evaluate(self, environment: dict) -> NumericWrapper:
        for condition, scope in zip(self.conditions, self.branch_scopes):
            if condition.evaluate(environment):
                return scope.evaluate(environment)
        if self.else_scope is not None:
            return self.else_scope.evaluate(environment)

        return NumericWrapper(None)


class WhileNode(ASTRoot):
    def __init__(self, line: int, pos: int, condition=None, scope: ScopeNode = None):
        super().__init__(line, pos)
        self.condition = condition
        self.scope = scope

    def evaluate(self, environment: dict):
        result = NumericWrapper(None)
        while self.condition.evaluate(environment):
            result = self.scope.evaluate(environment)
        return result


class OperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator, operands=None, associativity=None):
        super().__init__(line, pos)
        self.operator = operator
        self.operands = operands or []
        self.associativity: Literal['left', 'right', 'no'] = associativity or 'left'

    def _evaluate_or(self, environment: dict):
        for operand in self.operands[:-1]:
            result = operand.evaluate(environment)
            if result:
                return result
        return self.operands[-1].evaluate(environment)

    def _evaluate_and(self, environment: dict):
        for operand in self.operands:
            result = operand.evaluate(environment)
            if not result:
                return result
        return self.operands[-1].evaluate(environment)

    def _evaluate_assignment(self, environment: dict):
        value = self.operands[-1].evaluate(environment)
        for identifier in reversed(self.operands[:-1]):
            if isinstance(identifier, IdentifierNode):
                environment[identifier.name] = value
            elif isinstance(identifier, OperatorNode):
                if identifier.operator not in ("$index", "$attr"):
                    raise DIRuntimeSyntaxError(self.line, self.pos, "cannot assign to this expression")

                inner_value = identifier.operands[0].evaluate(environment)
                if identifier.operator == "$index":
                    sub_operand_chain = chain.from_iterable(
                        (chain.from_iterable(identifier.operands[1:-1]), identifier.operands[-1][:-1])
                    )
                    last_sub_operand = identifier.operands[-1][-1]
                else:
                    sub_operand_chain = identifier.operands[1:-1]
                    last_sub_operand = identifier.operands[-1]

                try:
                    if identifier.operator == "$index":
                        for sub_operand in sub_operand_chain:
                            inner_value = inner_value[sub_operand.evaluate(environment)]
                        inner_value[last_sub_operand.evaluate(environment)] = value
                    else:
                        for sub_operand in sub_operand_chain:
                            inner_value = inner_value[sub_operand.name]

                        inner_value[last_sub_operand.name] = value
                except IndexError as e:
                    raise DIIndexError(self.line, self.pos, str(e))

            else:
                raise DIRuntimeSyntaxError(self.line, self.pos, f"cannot assign to expression here: {identifier}")
        return value

    def _evaluate_power(self, environment: dict):
        value = self.operands[-1].evaluate(environment)
        for operand in reversed(self.operands[:-1]):
            value = operand.evaluate(environment) ** value
        return value

    def _evaluate_bitwise_xor(self, environment: dict):
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value ^ operand.evaluate(environment)
        return value

    def _evaluate_bitwise_and(self, environment: dict):
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value & operand.evaluate(environment)
        return value

    def _evaluate_bitwise_or(self, environment: dict):
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value | operand.evaluate(environment)
        return value

    def _evaluate_func_call(self, environment: dict):
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            if not callable(value):
                raise DITypeError(self.line, self.pos, f'Not a function: {value}')
            value = value([o.evaluate(environment) for o in operand])
        return value

    def _evaluate_indexation(self, environment: dict):
        value = self.operands[0].evaluate(environment)
        try:
            for sub_operand in chain.from_iterable(self.operands[1:]):
                value = value[sub_operand.evaluate(environment)]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return value

    def _evaluate_attribute_access(self, environment: dict):
        print(self.operands)
        value = self.operands[0].evaluate(environment)
        try:
            for sub_operand in self.operands[1:]:
                value = value[sub_operand.name]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return value

    def evaluate(self, environment: dict):
        match self.operator:
            case 'or': return self._evaluate_or(environment)
            case 'and': return self._evaluate_and(environment)
            case ':=': return self._evaluate_assignment(environment)
            case '**': return self._evaluate_power(environment)
            case '^': return self._evaluate_bitwise_xor(environment)
            case '&': return self._evaluate_bitwise_and(environment)
            case '|': return self._evaluate_bitwise_or(environment)
            case '$func': return self._evaluate_func_call(environment)
            case '$index': return self._evaluate_indexation(environment)
            case '$attr': return self._evaluate_attribute_access(environment)


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
            lhs = value
        return lhs


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
        self.parent_scope = None

    def __repr__(self):
        return self.node_type() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: dict):
        def func(params):
            environment_copy = environment.copy()

            for (param, arg) in zip(self.params, params, strict=True):
                environment_copy[param.name] = arg
            return self.body.evaluate(environment_copy)
        return FunctionWrapper(func)


class ClassDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode):
        super().__init__(line, pos)
        self.params = params
        self.body = scope

    def __repr__(self):
        return self.node_type() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: dict):
        def func(params):
            env = environment.copy()
            for (param, arg) in zip(self.params, params, strict=True):
                env[param.name] = arg
            self.body.evaluate(env, False)
            return DictWrapper(env)
        return FunctionWrapper(func)


class EllipsisOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, lst):
        super().__init__(line, pos)
        self.elements = lst

    def evaluate(self, environment: dict, in_list=False):
        if in_list:
            return self.elements.evaluate(environment)
        raise DIRuntimeSyntaxError(self.line, self.pos, "Cannot use ellipsis here")


class NumberNode(ASTRoot):
    def __init__(self, line: int, pos: int, number):
        super().__init__(line, pos)
        self.number = number

    def evaluate(self, environment: dict):
        return NumericWrapper(self.number)


class BooleanNode(ASTRoot):
    def __init__(self, line: int, pos: int, value: str):
        super().__init__(line, pos)
        if value == 'true':
            self.value = True
        elif value == 'false':
            self.value = False
        else:
            raise NotImplementedError

    def evaluate(self, environment: dict):
        return NumericWrapper(int(self.value))


class NullNode(ASTRoot):
    def __init__(self, line: int, pos: int):
        super().__init__(line, pos)

    def evaluate(self, environment: dict):
        return NumericWrapper(None)


class StringNode(ASTRoot):
    def __init__(self, line: int, pos: int, string: str):
        super().__init__(line, pos)
        self.string = string

    def evaluate(self, environment: dict):
        return StringWrapper(self.string)


class ListNode(ASTRoot):
    def __init__(self, line: int, pos: int, elements):
        super().__init__(line, pos)
        self.elements = elements

    def evaluate(self, environment: dict):
        result = []
        for e in self.elements:
            if isinstance(e, EllipsisOperatorNode):
                result.extend(e.evaluate(environment, in_list=True))
            else:
                result.append(e.evaluate(environment))
        return ListWrapper(result)


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
