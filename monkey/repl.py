from monkey.lexer import Lexer
from monkey.tokens import TokenType
from monkey.parser import Parser
from monkey.myast import display
from monkey.object import Environment
from monkey.evaluator import Evaluator
from monkey.compiler import Compiler, Bytecode
from monkey.vm import VirtualMachine, GLOBALS_SIZE
from monkey.symbol_table import SymbolTable

MONKEY_FACE ='''
           __,__
  .--.  .-"     "-.  .--.
 / .. \/  .-. .-.  \/ .. \\
| |  '|  /   Y   \ |'   | |
| \   \  \ 0 | 0 / /    / |
 \ '- ,\.-"""""""-./, -' /
  ''-' /_   ^ ^   _\ '-''
      |  \._   _./  |
      \   \ '~' /   /
       '._ '-=-' _.'
          '-----'
'''

def print_parse_errors(errors):
    print(MONKEY_FACE)
    print('Whoops! We ran into some monkey business here!')
    print(' parser errors:')
    for msg in errors:
        print(f'\t{msg}\n')

def start():
    PROMPT = '>> '

    env = Environment()

    constants = []
    global_bindings = [None] * GLOBALS_SIZE
    symbol_table = SymbolTable()

    while True:
        text = input(PROMPT)

        if not text:
            continue

        lexer = Lexer(text)
        parser = Parser(lexer)
        program = parser.parse_program()

        if len(parser.errors) != 0:
            print_parse_errors(parser.errors)
            continue

        print(f'\nTokens:\n{" ".join([str(t) for t in parser.tokens])}\n')
        print(f'AST:\n{program}\n')
        print('Prettified:')
        display(program)
        print()


        compiler = Compiler()
        compiler.symbol_table = symbol_table
        compiler.constants = constants
        err = compiler.compile(program)
        if err is not None:
            print(f'compiler error: {err}')
            continue

        bytecode = compiler.bytecode()
        constants = bytecode.constants
        print(f'Instructions:\n{bytecode.instructions}')

        print('Constants:\n' + "\n".join([f'{i}: {c}' for i, c in enumerate(bytecode.constants)]) + '\n')

        machine = VirtualMachine(bytecode)
        machine.globals = global_bindings
        err = machine.run()
        if err is not None:
            print(f'vm error: {err}')
            continue

        last_popped = machine.last_popped_stack_elem()
        print(f'Value:\n{last_popped.inspect()}')

        # # This is the old interpreter code
        # evaluated = Evaluator().evaluate(program, env)
        # if evaluated is not None:
        #     print(f" Value: {evaluated.inspect()}")
        #     # print(evaluated.inspect())

        print()