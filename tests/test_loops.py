import pytest

from src.interpreter import MiniInterpreter


class TestLoops:

    interpreter = MiniInterpreter()

    def test_loop(self):
        code_1 = """
        a := [];
        i := 0;
        while (i < 10) {
            a := [...a, i];
            i := i + 1;
        }
        
        a;
        """

        code_2 = """
        m := [[0, 1, 2], [3], [], [4, 5, 6, 7], [8, 9]]
        a := [];
        i := -1;
        while (i < 4) a := [...a, ...m[i := i + 1]]
        """

        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        actual_value_1 = self.interpreter.execute(code_1)
        actual_value_2 = self.interpreter.execute(code_2)

        assert actual_value_1 == actual_value_2 == expected
