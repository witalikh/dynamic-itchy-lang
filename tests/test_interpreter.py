from src.interpreter import MiniInterpreter
import pytest


class TestInterpreterClass:

    interpreter = MiniInterpreter()

    def test_operator_precedence(self):
        formulae_and_expected = [
            ("2 + 2 * 2", 6),
            ("(2 + 2) * 2", 8)
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected

    def test_matrix_multiplication(self):
        formulae_and_expected = [
            ("[[1, 5], [2, 3], [4, -4]] @ [[-1, -1/2], [1, 3/2]]", [[4, 7], [1, 7/2], [-8, -8]]),
            ("[[1, 2, 3], [4, 5, 6]] @ [[0, -1], [-1, 0], [1, 1]]", [[1, 2], [1, 2]])
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected
