from typing import Union, List, Optional, LiteralString, TextIO
from .ast import ASTRoot


class _TreePrinter:

    _MIDDLE_VAR: LiteralString = '├──'
    _LAST_VAR: LiteralString = '└──'
    _EMPTY: LiteralString = '    '
    _GOING: LiteralString = '│   '

    _REDUNDANT_ATTRS = ('line', 'pos')

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

        res = repr(tree) + '\n'

        attrs = tree.__dict__.copy()
        for redundant_attr in _TreePrinter._REDUNDANT_ATTRS:
            attrs.pop(redundant_attr, None)

        if len(attrs) == 1 and res.find(str(next(iter(attrs.values()))), res.find('(')) != -1:
            return res

        arg_num = len(attrs)
        for index, (arg_name, arg_value) in enumerate(attrs.items()):
            arg_name = arg_name.lstrip("_")
            marker = cls._LAST_VAR if index == arg_num - 1 else cls._MIDDLE_VAR
            substr = cls.print_tree(arg_value, indent, index == arg_num - 1)
            res += f"{indent}{marker}{arg_name}: {substr}"
        return res


def get_ast_tree(tree: ASTRoot) -> str:
    return _TreePrinter.print_tree(tree)


def print_ast_tree(tree: ASTRoot, end=None, file: Optional[TextIO] = None, flush: bool = False):
    print(_TreePrinter.print_tree(tree), end=end, file=file, flush=flush)
