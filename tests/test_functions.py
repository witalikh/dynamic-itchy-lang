from src.interpreter import MiniInterpreter

import pytest
import math


class TestInterpreterClass:

    interpreter = MiniInterpreter()

    def test_function(self):
        code = """
        
        PI := 3.1415926535897932384626433832795028841971
        
        sin := function(x) {
            
            # shift value to [0; PI]
            while (x > PI) x := x - PI;
            while (x < 0) x := x + PI;
            
            # reduce to [0; PI/2]
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

