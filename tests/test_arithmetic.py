from src.interpreter import MiniInterpreter
import pytest


class TestInterpreterClass:

    interpreter = MiniInterpreter()

    def test_addition(self):
        formulae_and_expected = [
            ("2 + 3", 5),
            ("2 + 4 + 7", 13),
            ("-1 + -2 + 3", 0),
            ("1.25 + 8.75 + 2.5", 12.5),
            ("0.25 + 0.33", 0.25 + 0.33),
            ("0b1001011 + 0b10001", 0b1011100),
            ("1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1", 10),
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"

    def test_subtraction(self):
        formulae_and_expected = [
            ("3 - 2", 1),
            ("7 - 4 - 2", 13),
            ("-1 + -2 + 3", 0),
            ("0.25 + 0.33", 0.25 + 0.33),
            ("0b1001011 + 0b10001", 0b1011100),
            ("1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1", 10),
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"

    def test_operator_precedence(self):
        formulae_and_expected = [
            ("2 + 2 * 2", 6),
            ("(2 + 2) * 2", 8)
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"

    def test_matrix_multiplication(self):
        formulae_and_expected = [
            ("[[1, 5], [2, 3], [4, -4]] @ [[-1, -1/2], [1, 3/2]]", [[4, 7], [1, 7/2], [-8, -8]]),
            ("[[1, 2, 3], [4, 5, 6]] @ [[0, -1], [-1, 0], [1, 1]]", [[1, 2], [1, 2]])
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"
