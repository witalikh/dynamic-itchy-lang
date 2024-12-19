import pytest
import math

from src.interpreter import MiniInterpreter


class TestFunctions:

    interpreter = MiniInterpreter()

    def test_function(self):
        code = """
        
        PI := 3.1415926535897932384626433832795028841971
        
        sin := function(x) {
            
            ## shift value to [0; PI]
            while (x > PI) x := x - PI;
            while (x < 0) x := x + PI;
            
            ## reduce to [0; PI/2]
            if (x > PI / 2) x := PI - x;
            
            sum := 0;
            value := x;
            k := 0;
            
            while (k < 15) {
                sum := sum + value;
                k := k + 1;
                value := -value * x ** 2 / ((2 * k) * (2 * k + 1));
            }
            
            sum;
        }
        
        
        sin(PI / 6);
        """
        expected = math.sin(math.pi / 6)

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected

    def test_recursion(self):
        code = """
        fibonacci := function(n) if (n == 0 or n == 1) n else fibonacci(n - 2) + fibonacci(n - 1)
        
        fibonacci(7); 
        """
        expected = 13

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected

    def test_polymorphism(self):
        code = """
        
        range := function(a, ...args) {
            [start, stop, step, ..._] := if (#args == 0) [0, a, 1] elif (#args == 1) [a, ...args, 1] else [a, ...args];
            
            [result, i] := [[], start];
            while (i < stop) [result, i] := [[...result, i], i + step];
            result;
        }
        
        a := range(1, 10, 2);
        b := range(5);
        c := range(3, 8);
        
        [a, b, c]
        """
        expected = [
            [1, 3, 5, 7, 9],
            [0, 1, 2, 3, 4],
            [3, 4, 5, 6, 7],
        ]

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected


    def test_variadic(self):
        code = """

        range := function(a, ...args) {
            [start, stop, step, ..._] := if (#args == 0) [0, a, 1] elif (#args == 1) [a, ...args, 1] else [a, ...args];

            [result, i] := [[], start];
            while (i < stop) [result, i] := [[...result, i], i + step];
            result;
        }

        a := range(1, 10, 2);
        b := range(5);
        c := range(3, 8);

        [a, b, c]
        """
        expected = [
            [1, 3, 5, 7, 9],
            [0, 1, 2, 3, 4],
            [3, 4, 5, 6, 7],
        ]

        actual_value = self.interpreter.execute(code)
        assert actual_value == expected