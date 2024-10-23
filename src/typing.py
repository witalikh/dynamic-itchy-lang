from typing import Union, Callable


TResult = Union[None, bool, int, float, complex, str, dict, Callable, "ListWrapper"]


class ListWrapper:

    def __init__(self, literal: list):
        self.content = literal

    def __repr__(self):
        return f'L[{', '.join([repr(e) for e in self.content])}]'

    def __bool__(self) -> bool:
        return len(self.content) != 0

    def __int__(self) -> int:
        raise NotImplementedError

    def __len__(self):
        return len(self.content)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return ListWrapper(self.content[item])

        size = len(self.content)
        if -size <= item < size:
            return self.content[item]

        if size == 0:
            raise IndexError(
                f'array index {item} out of range.\n'
                f'Size of array is zero, thus it can\'t be indexed'
            )
        if size == 1:
            raise IndexError(
                f'array index {item} out of range.\n'
                f'Size of array is one, thus acceptable values are either 0 or -1, which give same result'
            )

        raise IndexError(
            f'array index {item} out of range.\n'
            f'Size of array is {size}, thus acceptable ranges are:\n'
            f'from 0 to {size - 1}, '
            f'or from {-size} to -1 for reversed array traversal'
        )

    def __setitem__(self, key, value):
        self.content[key] = value

    def __delitem__(self, key):
        del self.content[key]

    def __iter__(self):
        return iter(self.content)

    def __add__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for +: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for +: {len(self)} and {len(other)}")

        return ListWrapper([a + b for a, b in zip(self.content, other.content)])

    def __sub__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for -: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for -: {len(self)} and {len(other)}")

        return ListWrapper([a - b for a, b in zip(self.content, other.content)])

    def __mul__(self, other: TResult):
        if not isinstance(other, (ListWrapper, int)):
            raise TypeError(f"unsupported operand type(s) for *: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for *: {len(self)} and {len(other)}")

        if isinstance(other, ListWrapper):
            return ListWrapper([a * b for a, b in zip(self.content, other.content)])

        return ListWrapper([e * other for e in self.content])

    def __truediv__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for /: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for /: {len(self)} and {len(other)}")

        return ListWrapper([a / b for a, b in zip(self.content, other.content)])

    def __floordiv__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for //: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for //: {len(self)} and {len(other)}")

        return ListWrapper([a // b for a, b in zip(self.content, other.content)])

    def __mod__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for %: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for %: {len(self)} and {len(other)}")

        return ListWrapper([a % b for a, b in zip(self.content, other.content)])

    def __pow__(self, other: TResult, modulo=None):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for **: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for **: {len(self)} and {len(other)}")

        return ListWrapper([pow(a, b, modulo) for a, b in zip(self.content, other.content)])

    def __matmul__(self, other: TResult):

        n = len(self.content)
        k1 = len(self.content[0])
        k2 = len(other.content)
        m = max(map(len, other.content))

        if k1 != k2:
            raise ValueError(f"incompatible dimensions for matrices: {n}x{k1} and {k2}x{m}")
        k = k1

        result = ListWrapper([
            ListWrapper([self[i][0] * other[0][j] for j in range(m)]) for i in range(n)
        ])

        for i in range(n):
            for j in range(m):
                for t in range(1, k):
                    result[i][j] = result[i][j] + self[i][t] * other[t][j]

        return result

    def __pos__(self):
        return ListWrapper([+a for a in self.content])

    def __neg__(self):
        return ListWrapper([-a for a in self.content])

    def __invert__(self):
        return ListWrapper([~a for a in self.content])

    def __lshift__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for <<: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for <<: {len(self)} and {len(other)}")

        return ListWrapper([a << b for a, b in zip(self.content, other.content)])

    def __rshift__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for >>: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for >>: {len(self)} and {len(other)}")

        return ListWrapper([a >> b for a, b in zip(self.content, other.content)])

    def __and__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for &: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for &: {len(self)} and {len(other)}")

        return ListWrapper([a & b for a, b in zip(self.content, other.content)])

    def __or__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for |: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for |: {len(self)} and {len(other)}")

        return ListWrapper([a | b for a, b in zip(self.content, other.content)])

    def __xor__(self, other: TResult):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for ^: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for ^: {len(self)} and {len(other)}")

        return ListWrapper([a ^ b for a, b in zip(self.content, other.content)])

    def __lt__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content < other.content
        return self.content < other

    def __le__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content <= other.content
        return self.content <= other

    def __gt__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content > other.content
        return self.content > other

    def __ge__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content >= other.content
        return self.content >= other

    def __eq__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content == other.content
        return self.content == other

    def __ne__(self, other: TResult | list):
        if isinstance(other, ListWrapper):
            return self.content != other.content
        return self.content != other
