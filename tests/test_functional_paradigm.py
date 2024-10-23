import pytest
import math

from src.interpreter import MiniInterpreter


class TestFunctionalParadigm:
    interpreter = MiniInterpreter()
    interpreter.import_module("""
        map := function(func, iter) {
            i := -1;
            a := []; 
            while ((i := i + 1) < #iter) a := [...a, func(iter[i])];
        }
        
        filter := function(func, iter){
            i := -1;
            a := [];
            while ((i := i + 1) < #iter) if (func(iter[i])) a := [...a, iter[i]];
            a;
        }
            
        reduce := function(func, iter, start) {
            result := start;
            i := -1;
            while ((i := i + 1) < #iter) result := func(result, iter[i]);
            result;
        }
    """
    )

    def test_map(self):
        code = "map(function(x) x ** 2, [1, 0, -3, -5, 6])"
        expected = [1, 0, 9, 25, 36]

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected

    def test_reduce(self):
        code = """reduce(function(acc, x) acc + x ** 2, [3, -1, -3, 0, 4, 6, -3], 0)"""
        expected = 80

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected

    def test_sum(self):
        code = """
            sum := function(iter, start) reduce(function (x, y) x + y, iter, start)
            sum([-1, 0, 2, 5, 7.5, 2.5, -3.5, -0.25, 3/4], 0)
        """
        expected = 13

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected
