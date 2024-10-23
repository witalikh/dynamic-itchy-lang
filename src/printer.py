from typing import Union, List, Optional, LiteralString
from .ast import ASTRoot


class TreePrinter:

    _MIDDLE_VAR: LiteralString = '├──'
    _LAST_VAR: LiteralString = '└──'
    _EMPTY: LiteralString = '    '
    _GOING: LiteralString = '│   '

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
        arg_num = len(attrs)
        for index, (arg_name, arg_value) in enumerate(attrs.items()):
            arg_name = arg_name.lstrip("_")
            marker = cls._LAST_VAR if index == arg_num - 1 else cls._MIDDLE_VAR
            substr = cls.print_tree(arg_value, indent, index == arg_num - 1)
            res += f"{indent}{marker}{arg_name}: {substr}"
        return res
