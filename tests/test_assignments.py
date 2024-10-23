import pytest

from src.interpreter import MiniInterpreter


class TestAssignment:

    interpreter = MiniInterpreter()

    def test_simple_straight_assignment(self):
        formulae_and_expected = [
            ("a := 13; 2 * a", 26),
            ("b := [\"Alice\", \"Bob\", \"Eve\"]; b[1]", "Bob"),
            ("a := 2 + 2 * 2; b := (2 + 2) * 2; b - a", 2),
            ("strangely_namedVariable123 := [1, 2+2, 3*3, 4*4];\n"
             "strangely_namedVariable123[2] + strangely_namedVariable123[3]", 25)
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"

    def test_list_straight_assignment(self):
        formulae_and_expected = [
            ("[a, b, c] := [1, 2, 3]; a + b * c", 7),
            ("[a, b, c, d, e] := [1, 4, 9, 16, 25]; e - d - c + b - a", 3),
            ("[a, b] := \"cd\"; a", "c")
        ]
        for idx, (formula, expected) in enumerate(formulae_and_expected):
            actual_value = self.interpreter.execute(formula)
            assert actual_value == expected, f"test #{idx} failed"

    def test_nested_listic_assignment(self):
        code = """
            aa := [1, 1, 2, 3, 4, 5, 2, 3]
            cd := ([a, ...[...b, c], d, e] := aa)
            b
        """
        expected = [1, 2, 3, 4]

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected
