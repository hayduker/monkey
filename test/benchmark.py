import argparse, sys, time

from monkey.lexer import Lexer
from monkey.parser import Parser
from monkey.compiler import Compiler
from monkey.vm import VirtualMachine
from monkey.object import Environment
from monkey.evaluator import Evaluator


input_string = '''
    let fibonacci = fn(x) {
        if (x == 0) {
            return 0;
        } else {
            if (x == 1) {
                return 1;
            } else {
                fibonacci(x - 1) + fibonacci(x - 2);
            }
        }
    };

    fibonacci(30);
    '''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-eng", "--engine", help="Use 'vm' or 'eval")

    args = parser.parse_args()

    print(f'Computing fionacci benchmark with engine={args.engine}')

    print('Lexing input...')
    lexer = Lexer(input_string)

    print('Parsing tokens...')
    parser = Parser(lexer)
    program = parser.parse_program()

    if args.engine == 'vm':
        print('Compiling AST...')
        compiler = Compiler()
        err = compiler.compile(program)
        if err is not None:
            print(f'compiler error: {err}')
            sys.exit(1)

        print('Executing bytecode in VM...')
        machine = VirtualMachine(compiler.bytecode())

        start = time.time()

        err = machine.run()
        if err is not None:
            print(f'vm error: {err}')
            sys.exit(1)
        
        duration = time.time() - start

        result = machine.last_popped_stack_elem()
    
    else:
        env = Environment()
        evaluator = Evaluator()
        
        start = time.time()

        print('Evaluating AST...')
        result = evaluator.evaluate(program, env)

        duration = time.time() - start
    
    print(f'engine={args.engine}, result={result}, duration={duration}')
