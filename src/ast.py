import itertools


from abc import ABC, abstractmethod
from itertools import pairwise
from typing import Optional, List, Dict, LiteralString, Union, Iterator

from src.exceptions import (
    DIRuntimeSyntaxError, DITypeError, DIZeroDivisionError,
    DINameError, DIValueError, DIIndexError, DIFunctionArgsCountError
)
from src.wrappers import (
    AbstractTypeWrapper,
    NumericWrapper, ListWrapper, StringWrapper, DictWrapper, FunctionWrapper
)


class ASTRoot(ABC):

    _MIDDLE_VAR: LiteralString = '├──'
    _LAST_VAR: LiteralString = '└──'
    _EMPTY: LiteralString = '    '
    _GOING: LiteralString = '│   '

    def __init__(self, line: int, pos: int) -> None:
        self.line = line
        self.pos = pos

    @classmethod
    def print_tree(
        cls,
        tree: Union["ASTRoot", List["ASTRoot"]],
        indent: str = "",
        last: Optional[bool] = None,
    ) -> str:
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

    def __repr__(self) -> str:
        return self.node_type()

    def node_type(self) -> str:
        return type(self).__name__.replace("Node", "")

    @abstractmethod
    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        pass


class ScopeNode(ASTRoot):
    def __init__(self, line: int, pos: int) -> None:
        super().__init__(line, pos)
        self.instructions = []

    def evaluate(self, environment: Dict, flush_variables: bool = True) -> AbstractTypeWrapper:
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
    def __init__(self, line: int, pos: int) -> None:
        super().__init__(line, pos)
        self.conditions: List[ASTRoot] = []
        self.branch_scopes: List[ScopeNode] = []
        self.else_scope: Optional[ScopeNode] = None

    def add_branch(self, condition: Optional[ASTRoot], scope: ScopeNode) -> None:
        if condition is None:
            self.else_scope = scope
        else:
            self.conditions.append(condition)
            self.branch_scopes.append(scope)

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        for condition, scope in zip(self.conditions, self.branch_scopes):
            if condition.evaluate(environment):
                return scope.evaluate(environment)
        if self.else_scope is not None:
            return self.else_scope.evaluate(environment)

        return NumericWrapper(None)


class WhileNode(ASTRoot):
    def __init__(self, line: int, pos: int, condition: ASTRoot, scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.condition = condition
        self.scope = scope

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        result = NumericWrapper(None)
        while self.condition.evaluate(environment):
            result = self.scope.evaluate(environment)
        return result


class AssignmentNode(ASTRoot):
    def __init__(self, line: int, pos: int, operands: List[ASTRoot], orders: List[bool]) -> None:
        super().__init__(line, pos)
        self.chain_of_assignments: List[ASTRoot] = operands or []
        self.chain_of_orders = orders or []

    @staticmethod
    def perform_assignment(
            lhs: ASTRoot,
            rhs: ASTRoot,
            return_old: bool,
            environment: Dict
    ) -> AbstractTypeWrapper:
        if isinstance(lhs, IdentifierNode):
            return AssignmentNode.assign_identifier(lhs, rhs, return_old, environment)
        if isinstance(lhs, OperatorNode):
            if lhs.operator == '$index':
                return AssignmentNode.assign_indexation(lhs, rhs, return_old, environment)
            if lhs.operator == "$attr":
                return AssignmentNode.assign_member(lhs, rhs, return_old, environment)
        if isinstance(lhs, ListNode):
            return AssignmentNode.assign_list(lhs, rhs, return_old, environment)
        raise ValueError(f"cannot assign to expression here: {lhs}")

    @staticmethod
    def assign_identifier(
            lhs: "IdentifierNode",
            rhs: ASTRoot,
            return_old: bool,
            environment: Dict
    ) -> AbstractTypeWrapper:
        new_value = rhs.evaluate(environment)
        if return_old:
            old_value = environment[lhs.name]
            environment[lhs.name] = new_value
            return old_value
        else:
            environment[lhs.name] = new_value
            return new_value

    @staticmethod
    def assign_list(
            lhs: "ListNode",
            rhs: ASTRoot,
            return_old: bool,
            environment: Dict
    ) -> AbstractTypeWrapper:
        if not isinstance(rhs, (ListNode, ListWrapper)):
            raise DIRuntimeSyntaxError(
                lhs.line, lhs.pos,
                f"cannot unpack non-iterable {type(rhs)} object")
        if len(lhs) < len(rhs):
            # TODO: unpacking operator support
            raise DIRuntimeSyntaxError(
                lhs.line, lhs.pos,
                f"too many values to unpack (expected {len(lhs)}, got {len(rhs)})")
        if len(lhs) > len(rhs):
            raise DIRuntimeSyntaxError(
                lhs.line, lhs.pos,
                f"not enough values to unpack (expected {len(lhs)}, got {len(rhs)})")

        for i, v in zip(lhs, rhs, strict=True):
            AssignmentNode.perform_assignment(i, v, return_old, environment)
        return rhs

    @staticmethod
    def assign_indexation(
            lhs: "OperatorNode",
            rhs: ASTRoot,
            return_old: bool,
            environment: Dict
    ) -> AbstractTypeWrapper:
        primary, *intermediate, last = lhs.operands
        value = primary.evaluate(environment)

        for i in intermediate:
            value = value[i.evaluate(environment)]

        new_value = rhs.evaluate(environment)
        if return_old:
            old_value = value[last.evaluate(environment)]
            value[last.evaluate(environment)] = new_value
            return old_value
        else:
            value[last.evaluate(environment)] = new_value
            return new_value

    @staticmethod
    def assign_member(
            lhs: "OperatorNode",
            rhs: ASTRoot,
            return_old: bool,
            environment: Dict
    ) -> AbstractTypeWrapper:
        primary, *intermediate, last = lhs.operands
        value = primary.evaluate(environment)

        for i in intermediate:
            value = value[i.name]

        new_value = rhs.evaluate(environment)
        if return_old:
            old_value = value[last.name]
            value[last.name] = new_value
            return old_value
        else:
            value[last.name] = new_value
            return new_value

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        rhs = self.chain_of_assignments[-1]
        try:
            for identifier, return_old in zip(reversed(self.chain_of_assignments[:-1]), reversed(self.chain_of_orders)):
                rhs = self.perform_assignment(identifier, rhs, return_old, environment)
        except ValueError as e:
            raise DIRuntimeSyntaxError(self.line, self.pos, str(e))
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return rhs


class OperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator: LiteralString, operands: List[Union[ASTRoot]]) -> None:
        super().__init__(line, pos)
        self.operator: LiteralString = operator
        self.operands: List[ASTRoot] = operands
        """
        $ index: list of lists of ...
        $ attr: list of Identifier Nodes
        """

    def evaluate_or(self, environment: Dict) -> AbstractTypeWrapper:
        for operand in self.operands[:-1]:
            result = operand.evaluate(environment)
            if result:
                return result
        return self.operands[-1].evaluate(environment)

    def evaluate_and(self, environment: Dict) -> AbstractTypeWrapper:
        for operand in self.operands:
            result = operand.evaluate(environment)
            if not result:
                return result
        return self.operands[-1].evaluate(environment)

    def evaluate_power(self, environment: Dict) -> AbstractTypeWrapper:
        value = self.operands[-1].evaluate(environment)
        for operand in reversed(self.operands[:-1]):
            value = operand.evaluate(environment) ** value
        return value

    def evaluate_bitwise_xor(self, environment: Dict) -> AbstractTypeWrapper:
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value ^ operand.evaluate(environment)
        return value

    def evaluate_bitwise_and(self, environment: Dict) -> AbstractTypeWrapper:
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value & operand.evaluate(environment)
        return value

    def evaluate_bitwise_or(self, environment: Dict) -> AbstractTypeWrapper:
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            value = value | operand.evaluate(environment)
        return value

    def evaluate_func_call(self, environment: Dict) -> AbstractTypeWrapper:
        value = self.operands[0].evaluate(environment)
        for operand in self.operands[1:]:
            if not callable(value):
                raise DITypeError(self.line, self.pos, f'Not a function: {value}')
            value = value([o.evaluate(environment) for o in operand])
        return value

    def evaluate_indexation(self, environment: Dict) -> AbstractTypeWrapper:
        primary, *indexers = self.operands
        value = primary.evaluate(environment)
        try:
            for index in itertools.chain.from_iterable(indexers):
                value = value[index.evaluate(environment)]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return value

    def evaluate_member_access(self, environment: Dict) -> AbstractTypeWrapper:
        primary, *indexers = self.operands
        value = primary.evaluate(environment)
        try:
            for indexer in indexers:
                value = value[indexer.name]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return value

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        match self.operator:
            case 'or': return self.evaluate_or(environment)
            case 'and': return self.evaluate_and(environment)
            case '**': return self.evaluate_power(environment)
            case '^': return self.evaluate_bitwise_xor(environment)
            case '&': return self.evaluate_bitwise_and(environment)
            case '|': return self.evaluate_bitwise_or(environment)
            case '$func': return self.evaluate_func_call(environment)
            case '$index': return self.evaluate_indexation(environment)
            case '$attr': return self.evaluate_member_access(environment)


class ComparisonNode(ASTRoot):
    def __init__(self, line: int, pos: int, operators: List[str], operands: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.operators = operators
        self.operands = operands

    # TODO: wrapper
    def evaluate(self, environment: Dict) -> bool:

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


class LeftPolyOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operators: List[str], operands: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.operators = operators
        self.operands = operands

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:

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
    def __init__(self, line: int, pos: int, operator: str, operand: ASTRoot) -> None:
        super().__init__(line, pos)
        self.operator = operator
        self.operand = operand

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        if self.operator == '-':
            return -self.operand.evaluate(environment)
        elif self.operator == '+':
            return self.operand.evaluate(environment)
        elif self.operator == '~':
            return ~self.operand.evaluate(environment)
        elif self.operator == 'not':
            return not self.operand.evaluate(environment)
        elif self.operator == '#':
            return NumericWrapper(len(self.operand.evaluate(environment)))

        raise NotImplemented


class FunctionDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.params = params
        self.body = scope
        self.parent_scope = None

    def __repr__(self) -> str:
        return self.node_type() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: Dict) -> FunctionWrapper:
        def func(params):
            environment_copy = environment.copy()
            try:
                for (param, arg) in zip(self.params, params, strict=True):
                    environment_copy[param.name] = arg
                return self.body.evaluate(environment_copy)
            except ValueError as e:
                # TODO:
                #  1. get rid of all wrappers
                #  2. better msg info
                raise DIFunctionArgsCountError(self.line, self.pos, str(e))
        return FunctionWrapper(func)


class ClassDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.params = params
        self.body = scope

    def __repr__(self) -> str:
        return self.node_type() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: Dict) -> FunctionWrapper:
        def func(params):
            env = environment.copy()
            for (param, arg) in zip(self.params, params, strict=True):
                env[param.name] = arg
            self.body.evaluate(env, False)
            return DictWrapper(env)
        return FunctionWrapper(func)


class EllipsisOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, list_value: "ListNode") -> None:
        super().__init__(line, pos)
        self.elements = list_value

    def evaluate(self, environment: Dict, in_list: bool = False) -> ListWrapper:
        if in_list:
            return self.elements.evaluate(environment)
        raise DIRuntimeSyntaxError(self.line, self.pos, "Cannot use ellipsis here")


class NumberNode(ASTRoot):
    def __init__(self, line: int, pos: int, number: Union[int, float, complex]) -> None:
        super().__init__(line, pos)
        self.number = number

    def evaluate(self, environment: Dict) -> NumericWrapper:
        return NumericWrapper(self.number)


class BooleanNode(ASTRoot):
    def __init__(self, line: int, pos: int, value: str) -> None:
        super().__init__(line, pos)
        if value == 'true':
            self.value = True
        elif value == 'false':
            self.value = False
        else:
            raise NotImplementedError

    def evaluate(self, environment: Dict) -> NumericWrapper:
        return NumericWrapper(int(self.value))


class NullNode(ASTRoot):
    def __init__(self, line: int, pos: int) -> None:
        super().__init__(line, pos)

    def evaluate(self, environment: Dict) -> NumericWrapper:
        return NumericWrapper(None)


class StringNode(ASTRoot):
    def __init__(self, line: int, pos: int, string: str) -> None:
        super().__init__(line, pos)
        self.string = string

    def evaluate(self, environment: Dict) -> StringWrapper:
        return StringWrapper(self.string)


class ListNode(ASTRoot):
    def __init__(self, line: int, pos: int, elements: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.elements = elements

    def __iter__(self) -> Iterator[ASTRoot]:
        return iter(self.elements)

    def __len__(self) -> int:
        return len(self.elements)

    def __getitem__(self, item: int) -> ASTRoot:
        return self.elements[item]

    def evaluate(self, environment: Dict) -> ListWrapper:
        result = []
        for e in self.elements:
            if isinstance(e, EllipsisOperatorNode):
                result.extend(e.evaluate(environment, in_list=True))
            else:
                result.append(e.evaluate(environment))
        return ListWrapper(result)


class IdentifierNode(ASTRoot):

    def __init__(self, line: int, pos: int, name: str) -> None:
        super().__init__(line, pos)
        self.name = name

    def __repr__(self) -> str:
        return self.node_type() + f'({self.name})'

    def evaluate(self, environment: Dict) -> AbstractTypeWrapper:
        if self.name in environment:
            return environment[self.name]
        raise DINameError(self.line, self.pos, f"Variable {self.name} is not defined")
