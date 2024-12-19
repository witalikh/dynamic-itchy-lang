## Just another one programming language 

Smaller, and tbh, more consistent.  
This project is not only about interpreter and language 
But rather about other stuff that happens in software engineering. So far here:
 - pytest + coverage
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
Update: at least in Python AST-interpreter version and other future interpreter declared dynamic it will so

### Operators
Standard as in many C-like languages, but:  
1. `#` is a length operator (lists, strings, etc)
2. `...a` is unpacking list operator
3. Assignments are `:=` and `=:`, the only difference is that last one returns old value   
in moment of assignment before actual assignment
4. `and`, `or`, and `?` (coalesce) operators are just `first false else last`, `first true else last` and
`first not-null else last` operators

Full list of operators (at least for now), sorted by precedence:

| #  | Group                   | Op   | A    | Description                          | Note: |
|----|-------------------------|------|------|--------------------------------------|-------|
| -1 | Comma                   | ,    | ->   |                                      |       |
| 00 | Assignment              | :=   | <-   | Assign and return new value          |       |
|    |                         | =:   |      | Assign and return old value          | [1]   |
| 01 | Coalesce                | ?    | ->   | First non-`null` value else last     |       |
| 02 | Logical                 | or   | . <- | First `true` value else last         |       |
| 03 |                         | xor  | . -> |                                      |       |
| 04 |                         | and  | . <- | First `false` value else last        |       |
| 05 |                         | not  | .    | The negation of value casted to bool |       |
| 06 | Comparison              | \>   | . .  | Greater than                         |       |
|    |                         | \<   | . .  | Lesser than                          |       |
|    |                         | \>=  | . .  | Greater than or equal                |       |
|    |                         | \<=  | . .  | Lesser than or equal                 |       |
|    |                         | ==   | . .  | Equal                                |       |
|    |                         | !=   | . .  | Not equal                            |       |
| 07 | Bitwise boolean algebra | \|   |      | Bitwise `or`                         |       |
| 08 |                         | \^   |      | Bitwise `xor`                        |       |
| 09 |                         | \&   |      | Bitwise `and`                        |       |
| 10 | Bitwise shifts          | \<\< | ->   | Bitwise left shift                   |       |
|    | Bitwise shifts          | \>\> | ->   | Bitwise right shift                  |       |
| 11 | Math additive           | +    |      | Addition                             |       |
|    | Math additive           | -    |      | Subtraction                          |       |
| 12 | Math multiplicative     | *    |      | Multiplication                       |       |
|    | Math multiplicative     | /    |      | Division                             |       |
|    | Math multiplicative     | //   |      | Floor division                       |       |
|    | Math multiplicative     | %    |      | Modulo                               |       |
|    | Math multiplicative     | **   |      | Power                                |       |
|    | Math multiplicative     | @    |      | Matrix multiplication                |       |
| 13 | Math multiplicative     |      |      |                                      |       |


[1] - Undefined variable counterparts return `null`