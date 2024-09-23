"""
Because this language is too dynamic, and right now
I'm too lazy to even bother about infinite cases of operators behaviour,
for sake of simplicity, and sacrificing with extra computational resources,
I made a 'common type' that combines all types into one.
"""

from copy import copy
from typing import Self


class LiteralWrapper:

    NULL = 'null'
    NUMERIC = 'numeric'
    LIST = 'list'

    def __init__(self, literal):
        if isinstance(literal, list):
            self.type = LiteralWrapper.LIST
        elif literal is None:
            self.type = LiteralWrapper.NULL
        else:
            self.type = LiteralWrapper.NUMERIC

        literal = literal if not None else 0
        self.content = literal

    def __repr__(self):
        if self.type == LiteralWrapper.NUMERIC:
            return f'W({self.content})'
        else:
            return f'W[{', '.join([repr(e) for e in self.content])}]'

    def unwrap(self):
        if self.type == LiteralWrapper.NUMERIC:
            return self.content
        else:
            return [e.unwrap() for e in self.content]

    def copy_with_capacity(self: Self, other: "LiteralWrapper") -> "LiteralWrapper":
        if self.type == other.type:
            if self.type != LiteralWrapper.LIST or len(self.content) > len(other.content):
                return LiteralWrapper(copy(self.content))
            else:
                self.content: list
                return LiteralWrapper(self.content + [0] * (len(other.content) - len(self.content)))

        # implies that 'other' is atomic
        if self.type == LiteralWrapper.LIST:
            return LiteralWrapper(copy(self.content))

        return LiteralWrapper([self.content] + [0] * (max(len(other.content) - 1, 0)))

    def __bool__(self) -> bool:
        if self.type == LiteralWrapper.NULL:
            return False

        if self.type == LiteralWrapper.NUMERIC:
            return self.content != 0 and self.content != float('nan')

        return len(self.content) != 0

    def __int__(self) -> int:
        if self.type == LiteralWrapper.NULL:
            return 0
        
        return int(self.content)

    def __len__(self):
        if self.type == LiteralWrapper.NULL:
            return 0
        elif self.type == LiteralWrapper.NUMERIC:
            return 1
        else:
            return len(self.content)

    def __getitem__(self, item):
        if self.type != LiteralWrapper.LIST:
            raise TypeError(f'{self.type} object ({self}) is not subscriptable')
        else:
            size = len(self.content)
            if -size <= item < size:
                return self.content[item]
            else:
                if size == 0:
                    raise IndexError(
                        f'array index {item} out of range.\n'
                        f'Size of array is zero, thus it can\'t be indexed'
                    )
                elif size == 1:
                    raise IndexError(
                        f'array index {item} out of range.\n'
                        f'Size of array is one, thus acceptable values are either 0 or -1, which give same result'
                    )
                else:
                    raise IndexError(
                        f'array index {item} out of range.\n'
                        f'Size of array is {size}, thus acceptable ranges are:\n'
                        f'from 0 to {size - 1}, '
                        f'or from {-size} to -1 for reversed array traversal'
                    )
                # return LiteralWrapper(0)

    def __setitem__(self, key, value):
        if self.type != LiteralWrapper.LIST:
            raise TypeError(f'{self.type} object ({self}) does not support item assignment')
        else:
            self.content[key] = value

    def __delitem__(self, key):
        if self.type != LiteralWrapper.LIST:
            raise TypeError(f'{self.type} object ({self}) does not support item deletion')
        else:
            del self.content[key]

    def __add__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content += other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] += other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] += elem
        return result

    def __sub__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content -= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] -= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] -= elem
        return result

    def __mul__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content *= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] *= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] *= elem
        return result

    def __truediv__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content /= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] /= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] /= elem
        return result

    def __floordiv__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content //= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] //= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] //= elem
        return result

    def __mod__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content %= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] %= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] %= elem
        return result

    def __pow__(self, other: Self, modulo=None):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content = pow(result.content, other.content, modulo)
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] = pow(result.content[0], other.content, modulo)
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] = pow(result.content[idx], elem, modulo)
        return result

    def __matmul__(self, other: Self):

        # res: atom <==> a: atom + b: atom
        if not (self.type == other.type == LiteralWrapper.LIST):
            raise ValueError("Non-matrices multiplication is forbidden")

        n = len(self.content)
        k1 = len(self.content[0])
        k2 = len(other.content)
        m = max(map(len, other.content))

        if k1 != k2:
            raise ValueError(f"Incompatible dimensions for matrices: {n}x{k1} and {k2}x{m}")
        k = k1

        result = LiteralWrapper(
            [LiteralWrapper([LiteralWrapper(0) for _ in range(m)]) for _ in range(n)]
        )

        for i in range(n):
            for j in range(m):
                for t in range(k):
                    result[i][j] += self[i][t] * other[t][j]

        return result

    def __pos__(self):
        return self

    def __neg__(self):
        result = LiteralWrapper(self.content)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content *= -1
            return result

        for idx in range(len(result.content)):
            result.content[idx] *= -1
        return result

    def __invert__(self):
        result = LiteralWrapper(self.content)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content = ~result.content
            return result

        for idx in range(len(result.content)):
            result.content[idx] = ~result.content[idx]
        return result

    def __lshift__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content <<= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] <<= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] <<= elem
        return result

    def __rshift__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content >>= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] >>= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] >>= elem
        return result

    def __and__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content &= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] &= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] &= elem
        return result

    def __or__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content |= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] |= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] |= elem
        return result

    def __xor__(self, other: Self):
        result = self.copy_with_capacity(other)

        # res: atom <==> a: atom + b: atom
        if result.type != LiteralWrapper.LIST:
            result.content ^= other.content
            return result

        if other.type != LiteralWrapper.LIST:
            result.content[0] ^= other.content
            return result

        for idx, elem in enumerate(other.content):
            result.content[idx] ^= elem
        return result

    def __lt__(self, other: Self):
        if self.type == other.type:
            return self.content < other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] < other.content

        return self.content < [other.content]

    def __le__(self, other: Self):
        if self.type == other.type:
            return self.content <= other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] <= other.content

        return self.content <= [other.content]

    def __gt__(self, other: Self):
        if self.type == other.type:
            return self.content > other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] > other.content

        return self.content > [other.content]

    def __ge__(self, other: Self):
        if self.type == other.type:
            return self.content >= other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] >= other.content

        return self.content >= [other.content]

    def __eq__(self, other: Self):
        if self.type == other.type:
            return self.content == other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] == other.content

        return self.content == [other.content]

    def __ne__(self, other: Self):
        if self.type == other.type:
            return self.content != other.content

        if self.type != LiteralWrapper.LIST:
            return [self.content] != other.content

        return self.content != [other.content]

    # def __dotmul__(self, other: Self):
    #     # TODO: dot multiplication .*
    #     result = self.copy_with_buffer(other)
    #
    #     # res: atom <==> a: atom + b: atom
    #     if result.type != LiteralWrapper.LIST:
    #         result.content += other.content
    #         return result
    #
    #     if other.type != LiteralWrapper.LIST:
    #         result.content[0] += other.content
    #         return result
    #
    #     for idx, elem in enumerate(other.content):
    #         result.content[idx] += elem
    #     return result

    def apply(self, func):
        if self.type == LiteralWrapper.NUMERIC:
            return LiteralWrapper(func(self.content))
        return LiteralWrapper([a.apply(func) for a in self.content])
