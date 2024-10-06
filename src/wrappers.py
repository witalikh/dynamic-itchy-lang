from abc import ABC, abstractmethod


class AbstractTypeWrapper(ABC):

    def __init__(self, content):
        self.content = content

    def __lt__(self, other: "AbstractTypeWrapper"):
        return self.content < other.content

    def __le__(self, other: "AbstractTypeWrapper"):
        return self.content <= other.content

    def __gt__(self, other: "AbstractTypeWrapper"):
        return self.content > other.content

    def __ge__(self, other: "AbstractTypeWrapper"):
        return self.content >= other.content

    def __eq__(self, other: "AbstractTypeWrapper"):
        return self.content == other.content

    def __ne__(self, other: "AbstractTypeWrapper"):
        return self.content != other.content
    
    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def __iter__(self):
        return iter(self.content)

    @abstractmethod
    def __getitem__(self, item):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __delitem__(self, key):
        pass

    @abstractmethod
    def unwrap(self):
        pass

    @abstractmethod
    def apply(self, func, *args, **kwargs):
        pass


class NumericWrapper(AbstractTypeWrapper):

    def __init__(self, literal: int | float | complex | None | bool):
        super().__init__(literal)

    def __repr__(self):
        return f'W({self.content})'

    def unwrap(self):
        return self.content

    def __bool__(self) -> bool:
        return self.content != 0

    def __int__(self) -> int:
        return int(self.content)

    def __len__(self):
        raise TypeError(f'numeric object ({self}) has no len')

    def __iter__(self):
        raise TypeError(f'numeric object ({self}) is not iterable')

    def __getitem__(self, item):
        raise TypeError(f'numeric object ({self}) is not subscriptable')

    def __setitem__(self, key, value):
        raise TypeError(f'numeric object ({self}) does not support item assignment')

    def __delitem__(self, key):
        raise TypeError(f'numeric object ({self}) does not support item deletion')

    def __add__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for +: {type(self)} and {type(other)}")
        return NumericWrapper(self.content + other.content)

    def __sub__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for -: {type(self)} and {type(other)}")
        return NumericWrapper(self.content - other.content)

    def __mul__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for *: {type(self)} and {type(other)}")
        return NumericWrapper(self.content * other.content)

    def __truediv__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for /: {type(self)} and {type(other)}")
        return NumericWrapper(self.content / other.content)

    def __floordiv__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for //: {type(self)} and {type(other)}")
        return NumericWrapper(self.content // other.content)

    def __mod__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for %: {type(self)} and {type(other)}")
        return NumericWrapper(self.content % other.content)

    def __pow__(self, other: AbstractTypeWrapper, modulo=None):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for **: {type(self)} and {type(other)}")
        return NumericWrapper(pow(self.content, other.content, modulo))

    def __pos__(self):
        return NumericWrapper(+self.content)

    def __neg__(self):
        return NumericWrapper(-self.content)

    def __invert__(self):
        return NumericWrapper(~self.content)

    def __lshift__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for <<: {type(self)} and {type(other)}")
        return NumericWrapper(self.content << other.content)

    def __rshift__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for >>: {type(self)} and {type(other)}")
        return NumericWrapper(self.content >> other.content)

    def __and__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for &: {type(self)} and {type(other)}")
        return NumericWrapper(self.content & other.content)

    def __or__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for |: {type(self)} and {type(other)}")
        return NumericWrapper(self.content | other.content)

    def __xor__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for ^: {type(self)} and {type(other)}")
        return NumericWrapper(self.content ^ other.content)

    def apply(self, func, *args, **kwargs):
        return NumericWrapper(func(self.content, *args, **kwargs))


class ListWrapper(AbstractTypeWrapper):

    def __init__(self, literal: list):
        super().__init__(literal)

    def __repr__(self):
        return f'L[{', '.join([repr(e) for e in self.content])}]'

    def unwrap(self):
        return [e.unwrap() for e in self.content]

    def __bool__(self) -> bool:
        return len(self.content) != 0

    def __int__(self) -> int:
        raise NotImplementedError

    def __len__(self):
        return len(self.content)

    def __getitem__(self, item):
        if isinstance(item, NumericWrapper):
            item = item.content

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
        if isinstance(key, NumericWrapper):
            key = key.content
        self.content[key] = value

    def __delitem__(self, key):
        if isinstance(key, NumericWrapper):
            key = key.content
        del self.content[key]

    def __iter__(self):
        return iter(self.content)

    def __add__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for +: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for +: {len(self)} and {len(other)}")

        return ListWrapper([a + b for a, b in zip(self.content, other.content)])

    def __sub__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for -: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for -: {len(self)} and {len(other)}")

        return ListWrapper([a - b for a, b in zip(self.content, other.content)])

    def __mul__(self, other: AbstractTypeWrapper):
        if not isinstance(other, (ListWrapper, NumericWrapper)):
            raise TypeError(f"unsupported operand type(s) for *: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for *: {len(self)} and {len(other)}")

        if isinstance(other, ListWrapper):
            return ListWrapper([a * b for a, b in zip(self.content, other.content)])

        return ListWrapper([e * other for e in self.content])

    def __truediv__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for /: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for /: {len(self)} and {len(other)}")

        return ListWrapper([a / b for a, b in zip(self.content, other.content)])

    def __floordiv__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for //: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for //: {len(self)} and {len(other)}")

        return ListWrapper([a // b for a, b in zip(self.content, other.content)])

    def __mod__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for %: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for %: {len(self)} and {len(other)}")

        return ListWrapper([a % b for a, b in zip(self.content, other.content)])

    def __pow__(self, other: AbstractTypeWrapper, modulo=None):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for **: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for **: {len(self)} and {len(other)}")

        return ListWrapper([pow(a, b, modulo) for a, b in zip(self.content, other.content)])

    def __matmul__(self, other: AbstractTypeWrapper):

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

    def __lshift__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for <<: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for <<: {len(self)} and {len(other)}")

        return ListWrapper([a << b for a, b in zip(self.content, other.content)])

    def __rshift__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for >>: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for >>: {len(self)} and {len(other)}")

        return ListWrapper([a >> b for a, b in zip(self.content, other.content)])

    def __and__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for &: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for &: {len(self)} and {len(other)}")

        return ListWrapper([a & b for a, b in zip(self.content, other.content)])

    def __or__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for |: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for |: {len(self)} and {len(other)}")

        return ListWrapper([a | b for a, b in zip(self.content, other.content)])

    def __xor__(self, other: AbstractTypeWrapper):
        if not isinstance(other, ListWrapper):
            raise TypeError(f"unsupported operand type(s) for ^: {type(self)} and {type(other)}")

        if len(self) != len(other):
            raise ValueError(f"different operands length for ^: {len(self)} and {len(other)}")

        return ListWrapper([a ^ b for a, b in zip(self.content, other.content)])

    def apply(self, func, *args, **kwargs):
        return ListWrapper([a.apply(func, *args, **kwargs) for a in self.content])


class StringWrapper(AbstractTypeWrapper):

    def __init__(self, literal: str):
        super().__init__(literal)

    def __repr__(self):
        return f'W("{self.content}")'

    def unwrap(self):
        return self.content

    def __bool__(self) -> bool:
        return self.content != ""

    def __int__(self) -> int:
        return int(self.content)

    def __len__(self):
        return len(self.content)

    def __getitem__(self, item):
        if isinstance(item, NumericWrapper):
            item = item.content

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
        self.content = self.content[:key] + value + self.content[key + 1:]

    def __delitem__(self, key):
        self.content = self.content[:key] + self.content[key + 1:]

    def __iter__(self):
        return iter(self.content)

    def __add__(self, other: AbstractTypeWrapper):
        if not isinstance(other, StringWrapper):
            raise TypeError(f"unsupported operand type(s) for +: {type(self)} and {type(other)}")
        return NumericWrapper(self.content + other.content)

    def __sub__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for -: {type(self)} and {type(other)}")

    def __mul__(self, other: AbstractTypeWrapper):
        if not isinstance(other, NumericWrapper):
            raise TypeError(f"unsupported operand type(s) for *: {type(self)} and {type(other)}")
        return StringWrapper(self.content * other.content)

    def __truediv__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for /: {type(self)} and {type(other)}")

    def __floordiv__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for //: {type(self)} and {type(other)}")

    def __mod__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for %: {type(self)} and {type(other)}")

    def __pow__(self, other: AbstractTypeWrapper, modulo=None):
        raise TypeError(f"unsupported operand type(s) for **: {type(self)} and {type(other)}")

    def __matmul__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for @: {type(self)} and {type(other)}")

    def __pos__(self):
        raise TypeError(f"unsupported operand type(s) for +: {type(self)}")

    def __neg__(self):
        raise TypeError(f"unsupported operand type(s) for -: {type(self)}")

    def __invert__(self):
        raise TypeError(f"unsupported operand type(s) for ~: {type(self)}")

    def __lshift__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for <<: {type(self)} and {type(other)}")

    def __rshift__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for >>: {type(self)} and {type(other)}")

    def __and__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for &: {type(self)} and {type(other)}")

    def __or__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for |: {type(self)} and {type(other)}")

    def __xor__(self, other: AbstractTypeWrapper):
        raise TypeError(f"unsupported operand type(s) for ^: {type(self)} and {type(other)}")

    def apply(self, func, *args, **kwargs):
        return StringWrapper(func(self.content))


class DictWrapper(AbstractTypeWrapper):

    def __init__(self, literal: dict):
        super().__init__(literal)

    def __repr__(self):
        return f'D[{',\n '.join([f'{repr(k)}: {repr(v)}' for k, v in self.content.items()])}]'

    def unwrap(self):
        return {k: v.unwrap() for k, v in self.content.items()}

    def __bool__(self) -> bool:
        return len(self.content) != 0

    def __int__(self) -> int:
        raise NotImplementedError

    def __len__(self):
        return len(self.content)

    def __getitem__(self, item):
        return self.content[item]

    def __setitem__(self, key, value):
        self.content[key] = value

    def __delitem__(self, key):
        del self.content[key]

    def __iter__(self):
        return iter(self.content)

    def apply(self, func, *args, **kwargs):
        return ListWrapper([a.apply(func, *args, **kwargs) for a in self.content])


class FunctionWrapper(AbstractTypeWrapper):

    def __init__(self, func_to_call):
        super().__init__(None)
        self.func = func_to_call

    def __repr__(self):
        return f'W({self.content})'

    def unwrap(self):
        return self.content

    def __bool__(self) -> bool:
        return self.content != 0

    def __int__(self) -> int:
        return int(self.content)

    def __len__(self):
        raise TypeError(f'numeric object ({self}) has no len')

    def __iter__(self):
        raise TypeError(f'numeric object ({self}) is not iterable')

    def __getitem__(self, item):
        raise TypeError(f'numeric object ({self}) is not subscriptable')

    def __setitem__(self, key, value):
        raise TypeError(f'numeric object ({self}) does not support item assignment')

    def __delitem__(self, key):
        raise TypeError(f'numeric object ({self}) does not support item deletion')

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def apply(self, func, *args, **kwargs):
        return NumericWrapper(func(self.content, *args, **kwargs))
