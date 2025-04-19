from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Union, Iterator, Callable, IO

from collections.abc import Sequence

from src.exceptions import (
    DIRuntimeSyntaxError, DITypeError, DIZeroDivisionError,
    DINameError, DIValueError, DIIndexError, DIFunctionArgsCountError
)
from src.typing import (
    TResult,
    ListWrapper
)


class ASTRoot(ABC):

    def __init__(self, line: int, pos: int) -> None:
        self.line = line
        self.pos = pos

    def __repr__(self) -> str:
        return type(self).__name__.replace("Node", "")

    @abstractmethod
    def evaluate(self, environment: Dict) -> TResult:
        pass

    @abstractmethod
    def serialize(self, stdout: IO) -> None:
        pass

    @staticmethod
    def evaluate_arg_list(args: list["ASTRoot"], environment: dict, allow_ellipsis: bool = True):
        result = []
        for arg in args:
            if isinstance(arg, EllipsisOperatorNode):
                result.extend(arg.evaluate(environment, allow_ellipsis))
            else:
                result.append(arg.evaluate(environment))
        return result


class ScopeNode(ASTRoot):
    def __init__(self, line: int, pos: int) -> None:
        super().__init__(line, pos)
        self.instructions: List[ASTRoot] = []

    def evaluate(self, environment: Dict, flush_variables: bool = True) -> TResult:
        old_environment = set(environment.keys())

        last = None
        for instruction in self.instructions:
            last = instruction.evaluate(environment)

        if flush_variables:
            redundant_variables = set(environment.keys())
            redundant_variables.difference_update(old_environment)
            for variable_to_delete in redundant_variables:
                environment.pop(variable_to_delete, None)

        return last

    def serialize(self, stdout: IO) -> None:
        # TODO: prototype, do real serialization
        for instruction in self.instructions:
            instruction.serialize(stdout)
            stdout.write('\n')


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

    def evaluate(self, environment: Dict) -> TResult:
        for condition, scope in zip(self.conditions, self.branch_scopes):
            if condition.evaluate(environment):
                return scope.evaluate(environment)
        if self.else_scope is not None:
            return self.else_scope.evaluate(environment)

        return None

    def serialize(self, stdout: IO) -> None:

        # TODO: serialization
        pass


class WhileNode(ASTRoot):
    def __init__(self, line: int, pos: int, condition: ASTRoot, scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.condition = condition
        self.scope = scope

    def evaluate(self, environment: Dict) -> TResult:
        result = None
        while self.condition.evaluate(environment):
            result = self.scope.evaluate(environment)
        return result

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class AssignmentNode(ASTRoot):
    def __init__(self, line: int, pos: int, lhs: ASTRoot, rhs: ASTRoot) -> None:
        super().__init__(line, pos)
        self.lhs = lhs
        self.rhs = rhs

    @staticmethod
    def evaluation_guard(value: Union[ASTRoot, TResult], environment: Dict) -> TResult:
        # TODO: crutch
        if isinstance(value, ASTRoot):
            return value.evaluate(environment)
        return value

    @staticmethod
    def perform_assignment(
            lhs: ASTRoot,
            rhs: Union[ASTRoot, TResult],
            environment: Dict
    ) -> TResult:
        if isinstance(lhs, IdentifierNode):
            return AssignmentNode.assign_identifier(lhs, rhs, environment)
        if isinstance(lhs, IndexationNode):
            return AssignmentNode.assign_indexation(lhs, rhs, environment)
        if isinstance(lhs, AttributeCallNode):
            return AssignmentNode.assign_member(lhs, rhs, environment)
        if isinstance(lhs, ListNode):
            return AssignmentNode.assign_list(lhs, rhs, environment)
        raise ValueError(f"cannot assign to expression here: {lhs}")

    @staticmethod
    def assign_identifier(
            lhs: "IdentifierNode",
            rhs: Union[ASTRoot, TResult],
            environment: Dict
    ) -> TResult:
        new_value = AssignmentNode.evaluation_guard(rhs, environment)
        environment[lhs.name] = new_value
        return new_value

    @staticmethod
    def _check_lhs_ellipses_for_list_assignment(
        lhs: Union["ListNode", list[Union["IdentifierNode", "EllipsisOperatorNode"]]],
        rhs
    ):

        ellipsis_exists = False
        rhs_ellipsis_element = None
        consumed_rhs_slice = None

        for idx, x in enumerate(lhs):
            if not isinstance(x, EllipsisOperatorNode):
                continue

            if ellipsis_exists:
               raise ValueError(f"too many unpacking expressions in assignment")
            ellipsis_exists = True

            rhs_ellipsis_element = x.elements
            # if not isinstance(rhs_ellipsis_element, IdentifierNode):
            #     pass
            consumed_rhs_slice = slice(idx, idx + len(rhs) - len(lhs) + 1)

        if (len(lhs) > len(rhs) and not ellipsis_exists) or len(lhs) > len(rhs) + 1:
            raise ValueError(f"not enough values to unpack (expected {len(lhs)}, got {len(rhs)})")

        if len(lhs) < len(rhs) and not ellipsis_exists:
            raise ValueError(f"too many values to unpack (expected {len(lhs)}, got {len(rhs)})")

        return ellipsis_exists, rhs_ellipsis_element, consumed_rhs_slice

    @staticmethod
    def _assign_to_list_with_ellipses(
            lhs: Union["ListNode", list[Union["IdentifierNode", "EllipsisOperatorNode"]]],
            rhs: Union[ASTRoot, TResult],
            ellipsis_assignee,
            slice_of_rhs: slice,
            environment: Dict,
    ) -> None:

        for idx in range(slice_of_rhs.start):
            AssignmentNode.perform_assignment(lhs[idx], rhs[idx], environment)

        AssignmentNode.perform_assignment(ellipsis_assignee, rhs[slice_of_rhs], environment)

        for l_idx, r_idx in zip(range(slice_of_rhs.start + 1, len(lhs)), range(slice_of_rhs.stop, len(rhs))):
            AssignmentNode.perform_assignment(lhs[l_idx], rhs[r_idx], environment)

    @staticmethod
    def assign_list(
            lhs: Union["ListNode", list[Union["IdentifierNode", "EllipsisOperatorNode"]]],
            rhs: Union[ASTRoot, TResult],
            environment: Dict,

    ) -> TResult:
        #
        rhs = AssignmentNode.evaluation_guard(rhs, environment)

        #ensure it's a list
        if not isinstance(rhs, Sequence):
            raise ValueError(f"cannot unpack non-iterable {type(rhs)} object")

        ellipsis_exists, ellipsis_assignee, slice_of_rhs = (
            AssignmentNode._check_lhs_ellipses_for_list_assignment(lhs, rhs))

        if ellipsis_exists:
            AssignmentNode._assign_to_list_with_ellipses(lhs, rhs, ellipsis_assignee, slice_of_rhs, environment)
            return rhs

        for i, v in zip(lhs, rhs):
            AssignmentNode.perform_assignment(i, v, environment)
        return rhs

    @staticmethod
    def assign_indexation(
            lhs: "IndexationNode",
            rhs: Union[ASTRoot, TResult],
            environment: Dict
    ) -> TResult:
        *intermediate, last = lhs.args
        value = lhs.iter.evaluate(environment)

        for i in intermediate:
            value = value[i.evaluate(environment)]

        new_value = AssignmentNode.evaluation_guard(rhs, environment)
        value[last.evaluate(environment)] = new_value
        return new_value

    @staticmethod
    def assign_member(
            lhs: "AttributeCallNode",
            rhs: Union[ASTRoot, TResult],
            environment: Dict
    ) -> TResult:
        value = lhs.obj.evaluate(environment)

        new_value = AssignmentNode.evaluation_guard(rhs, environment)
        value[lhs.member.name] = new_value
        return new_value

    def evaluate(self, environment: Dict) -> TResult:
        try:
            return self.perform_assignment(self.lhs, self.rhs, environment)
        except ValueError as e:
            raise DIRuntimeSyntaxError(self.line, self.pos, str(e))
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class OperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator: str, lhs: ASTRoot, rhs: ASTRoot) -> None:
        super().__init__(line, pos)
        self.lhs = lhs
        self.rhs = rhs
        self.operator = operator
        """
        $ index: list of lists of ...
        $ attr: list of Identifier Nodes
        """

    def evaluate_or(self, environment: Dict) -> TResult:
        return self.lhs.evaluate(environment) or self.rhs.evaluate(environment)

    def evaluate_and(self, environment: Dict) -> TResult:
        return self.lhs.evaluate(environment) and self.rhs.evaluate(environment)

    def evaluate_coalesce(self, environment: Dict) -> TResult:
        result = self.lhs.evaluate(environment)
        # TODO: NoneNode?
        if result is not None:
            return result
        return self.rhs.evaluate(environment)


    def evaluate(self, environment: Dict) -> TResult:
        match self.operator:
            case 'or':
                return self.evaluate_or(environment)
            case 'and':
                return self.evaluate_and(environment)
            case '?':
                return self.evaluate_coalesce(environment)
            case '**':
                return self.lhs.evaluate(environment) ** self.rhs.evaluate(environment)
            case '^':
                return self.lhs.evaluate(environment) ^ self.rhs.evaluate(environment)
            case '&':
                return self.lhs.evaluate(environment) & self.rhs.evaluate(environment)
            case '|':
                return self.lhs.evaluate(environment) | self.rhs.evaluate(environment)
            case '+':
                return self.lhs.evaluate(environment) + self.rhs.evaluate(environment)
            case '-':
                return self.lhs.evaluate(environment) - self.rhs.evaluate(environment)
            case '*':
                return self.lhs.evaluate(environment) * self.rhs.evaluate(environment)
            case '/':
                lhs = self.lhs.evaluate(environment)
                rhs = self.rhs.evaluate(environment)
                try:
                    return lhs / rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} / {rhs}.")

            case '//':
                lhs = self.lhs.evaluate(environment)
                rhs = self.rhs.evaluate(environment)
                try:
                    return lhs // rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} // {rhs}")

            case '%':
                lhs = self.lhs.evaluate(environment)
                rhs = self.rhs.evaluate(environment)
                try:
                    return lhs % rhs
                except ZeroDivisionError:
                    raise DIZeroDivisionError(self.line, self.pos, f"cannot divide: {lhs} % {rhs}")
            case '@':
                try:
                    return self.lhs.evaluate(environment) @ self.rhs.evaluate(environment)
                except TypeError as e:
                    raise DITypeError(self.line, self.pos, str(e)) from None
                except ValueError as e:
                    raise DIValueError(self.line, self.pos, str(e)) from None
            case '<<':
                return self.lhs.evaluate(environment) << self.rhs.evaluate(environment)
            case '>>':
                return self.lhs.evaluate(environment) >> self.rhs.evaluate(environment)


    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class FunctionCallNode(ASTRoot):
    def __init__(self, line: int, pos: int, func: ASTRoot, args: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.func = func
        self.args = args

    def evaluate(self, environment: Dict) -> TResult:
        func = self.func.evaluate(environment)

        if isinstance(self.func, AttributeCallNode):
            obj = self.func.obj.evaluate(environment)
            return func([obj] + ASTRoot.evaluate_arg_list(self.args, environment))

        if not callable(func):
            raise DITypeError(self.line, self.pos, f'Not a function: {func}')

        return func(ASTRoot.evaluate_arg_list(self.args, environment))

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class IndexationNode(ASTRoot):
    def __init__(self, line: int, pos: int, iter_: ASTRoot, args: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.iter = iter_
        self.args = args

    def evaluate(self, environment: Dict) -> TResult:
        value = self.iter.evaluate(environment)
        try:
            for index in self.args:
                value = value[index.evaluate(environment)]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))
        return value

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class AttributeCallNode(ASTRoot):
    def __init__(self, line: int, pos: int, obj: ASTRoot, member: "IdentifierNode") -> None:
        super().__init__(line, pos)
        self.obj = obj
        self.member = member

    def evaluate(self, environment: Dict) -> TResult:
        value = self.obj.evaluate(environment)
        try:
            return value[self.member.name]
        except IndexError as e:
            raise DIIndexError(self.line, self.pos, str(e))

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class ComparisonNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator: str, lhs: ASTRoot, rhs: ASTRoot) -> None:
        super().__init__(line, pos)
        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def evaluate(self, environment: Dict) -> bool:

        lhs = self.lhs.evaluate(environment)
        rhs = self.rhs.evaluate(environment)

        match self.operator:
            case '<=':
                return lhs <= rhs
            case '>=':
                return lhs >= rhs
            case '<':
                return lhs < rhs
            case '>':
                return lhs > rhs
            case '==':
                return lhs == rhs
            case '!=':
                return lhs != rhs
        return False

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class UnaryOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, operator: str, operand: ASTRoot) -> None:
        super().__init__(line, pos)
        self.operator = operator
        self.operand = operand

    def evaluate(self, environment: Dict) -> TResult:
        if self.operator == '-':
            return -self.operand.evaluate(environment)
        elif self.operator == '+':
            return self.operand.evaluate(environment)
        elif self.operator == '~':
            return ~self.operand.evaluate(environment)
        elif self.operator == 'not':
            return not self.operand.evaluate(environment)
        elif self.operator == '#':
            return len(self.operand.evaluate(environment))

        raise NotImplemented

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class FunctionDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.params = params
        self.body = scope

    def __repr__(self) -> str:
        return super().__repr__() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: Dict) -> Callable:
        def func(params):
            environment_copy = environment.copy()
            try:
                AssignmentNode.assign_list(self.params, params, environment_copy)
                return self.body.evaluate(environment_copy)
            except ValueError as e:
                # TODO:
                #  1. better msg info
                raise DIFunctionArgsCountError(self.line, self.pos, str(e))

        return func

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class ClassDeclarationNode(ASTRoot):
    def __init__(self, line: int, pos: int, params: list["IdentifierNode"], scope: ScopeNode) -> None:
        super().__init__(line, pos)
        self.params = params
        self.body = scope

    def __repr__(self) -> str:
        return super().__repr__() + f'(params count: {len(self.params)})'

    def evaluate(self, environment: Dict) -> Callable:
        def func(params):
            env = environment.copy()
            AssignmentNode.assign_list(self.params, params, env)
            # for (param, arg) in zip(self.params, params, strict=True):
            #     env[param.name] = arg
            self.body.evaluate(env, False)
            return env

        return func

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class EllipsisOperatorNode(ASTRoot):
    def __init__(self, line: int, pos: int, list_value: Union["ListNode", "IdentifierNode", "ASTRoot"]) -> None:
        super().__init__(line, pos)
        self.elements = list_value

    def __repr__(self):
        if isinstance(self.elements, IdentifierNode):
            return super().__repr__() + f'({self.elements.name})'
        return super().__repr__()

    def evaluate(self, environment: Dict, in_list: bool = False) -> ListWrapper:
        if in_list:
            return self.elements.evaluate(environment)
        raise DIRuntimeSyntaxError(self.line, self.pos, "Cannot use ellipsis here")

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class NumberNode(ASTRoot):
    def __init__(self, line: int, pos: int, number: Union[int, float, complex]) -> None:
        super().__init__(line, pos)
        self.number = number

    def __repr__(self):
        return super().__repr__() + f'({self.number})'

    def evaluate(self, environment: Dict):
        return self.number

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class BooleanNode(ASTRoot):
    def __init__(self, line: int, pos: int, value: str) -> None:
        super().__init__(line, pos)
        if value == 'true':
            self.value = True
        elif value == 'false':
            self.value = False
        else:
            raise NotImplementedError

    def __repr__(self):
        return super().__repr__() + f'({self.value})'

    def evaluate(self, environment: Dict) -> bool:
        return self.value

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class NullNode(ASTRoot):
    def __init__(self, line: int, pos: int) -> None:
        super().__init__(line, pos)

    def evaluate(self, environment: Dict) -> None:
        return None

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class StringNode(ASTRoot):
    def __init__(self, line: int, pos: int, string: str) -> None:
        super().__init__(line, pos)
        self.string = string

    def __repr__(self):
        return super().__repr__() + f'({self.string})'

    def evaluate(self, environment: Dict) -> str:
        return self.string

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class ListNode(ASTRoot):
    def __init__(self, line: int, pos: int, elements: List[ASTRoot]) -> None:
        super().__init__(line, pos)
        self.elements = elements

    def __repr__(self):
        return super().__repr__() + f'[count: {len(self.elements)}]'

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

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass


class IdentifierNode(ASTRoot):

    def __init__(self, line: int, pos: int, name: str) -> None:
        super().__init__(line, pos)
        self.name = name

    def __repr__(self) -> str:
        return super().__repr__() + f'({self.name})'

    def evaluate(self, environment: Dict) -> TResult:
        if self.name in environment:
            return environment[self.name]
        raise DINameError(self.line, self.pos, f"Variable {self.name} is not defined")

    def serialize(self, stdout: IO) -> None:
        # TODO: serialization
        pass
