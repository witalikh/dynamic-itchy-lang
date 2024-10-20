## Just another one programming language 

Smaller, and tbh, more consistent.  
This project is not only about interpreter and language 
But rather about other stuff that happens in software engineering. So far here:
 - pytest
 - CircleCI

## Dynamic Itchy
### Short introduction
0. Syntax. The snippet below 
```text
\* This is a multiline comment.
All comments can be inline as well.

By the way,
The code snippet is about the sum of `n` first prime numbers.
\*

sum := 0; \* Any assignment looks like this *\
i := 0  \* Semicolon is not required *\
n := 10; \* But it's better to write it when possible... *\

\* Functions are defined via assignment as well
is_prime := function(number) {
    if (n <= 1) {
        \* the only statement in this scope is a 'false' value.
         this will be returned in case of satisfying current branch condition *\
        false;
    }
    elif (n == 2) true \* if scope is one statement, it doesn't need braces *\
    elif (n % 2 == 0) false
    else {
        \* Use Eratosthenes' sift
        for odd numbers greater than one *\

        prime := true;
        divisor := 3;
        threshold := n ** .5;
        
        while (divisor <= threshold) {
            if (n % divisor == 0) {
                prime := false;
                
                \* stop loop by directly violating the condition *\
                divisor := n;
            } else {
                divisor := divisor + 2;
            }
        }
        
        \* return value *\
        prime;
    }
}

while (i <= n) {
    if (is_prime(i)) sum := sum + i
}

\* output 'sum' as program final result \*
sum
```
### Principles
1. Last expression is a result  
- The result of every scope is the last expression value in it  
- Empty scope or its absence returns `null`
- `if-elif-else` returns the value from scope of executed branch
- `while` loop returns last expression from scope, executed in last iteration
- Assignment like `a := <statement>` returns assigned value in `statement`  

2. There is nothing that cannot be assigned or be an operand of another operator  
    E.g.
    ```
   (fibonacci := function (n) if (n == 0 or n == 1) n else fibonacci(n - 2) + fibonacci(n - 1))(7) + fibonacci(11);
   ```
   is a valid code and returns `102` (as sum of seventh and eleventh number of Fibonacci sequence, `13` and `89`)

Drawbacks: forget about `break`, `continue`, `return` and any other control-flow statement.  
At least for now.  
3. Never type-checked until actual calculation  
Thus, if variable is already evaluated, no matter it placed it has value (see example above)

### Operators
Standard as in many C-like languages, but:  
1. `#` is a length operator (lists, strings, etc)
2. `...a` is unpacking list operator
3. Assignments are `:=` and `=:`, the only difference is that last one returns old value   
in moment of assignment before actual assignment
4. 