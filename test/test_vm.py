import unittest

from typing import List
from dataclasses import dataclass

from monkey import code
from monkey.object import *
from monkey.lexer import Lexer
from monkey.parser import Parser
from monkey.compiler import Compiler, Bytecode
from monkey.vm import VirtualMachine


@dataclass
class VmTestCase:
    input_string: str
    expected: Any


class TestCompiler(unittest.TestCase):
    def parse(self, input_string: str) -> ast.Program:
        lexer = Lexer(input_string)
        parser = Parser(lexer)
        return parser.parse_program()

    def check_integer_object(self, expected: int, actual: Object) -> None:
        self.assertIsInstance(actual, IntegerObject)
        self.assertEqual(actual.value, expected)

    def check_boolean_object(self, expected: bool, actual: Object) -> None:
        self.assertIsInstance(actual, BooleanObject)
        self.assertEqual(actual.value, expected)

    def check_expected_object(self, expected: Any, actual: Object) -> None:
        if expected is None:
            self.assertEqual(actual, NULL)
        elif type(expected) == int:
            self.check_integer_object(expected, actual)
        elif type(expected) == bool:
            self.check_boolean_object(expected, actual)
        elif type(expected) == list:
            self.assertIsInstance(actual, ArrayObject)
            self.assertEqual(len(actual.elements), len(expected))
            for i, elem in enumerate(expected):
                self.check_expected_object(elem, actual.elements[i])
        elif type(expected) == dict:
            self.assertIsInstance(actual, HashObject)
            self.assertEqual(len(actual.pairs), len(expected))
            for key, value in expected.items():
                key = IntegerObject(key)
                self.assertIn(key, actual.pairs)
                self.check_expected_object(value, actual.pairs[key])
        elif type(expected) == ErrorObject:
            if expected.message != actual.message:
                self.fail(f'wrong error message. expected={expected.message}, got={actual.message}')
    
    def run_vm_tests(self, tests: List[VmTestCase]) -> None:
        for test in tests:
            program = self.parse(test.input_string)
            compiler = Compiler()
            err = compiler.compile(program)
            if err is not None:
                self.fail(f'compiler error: {err}')
            
            vm = VirtualMachine(compiler.bytecode())
            err = vm.run()
            if err is not None:
                self.fail(f'vm error: {err}')
            
            stack_elem = vm.last_popped_stack_elem()
            self.check_expected_object(test.expected, stack_elem)

    def test_integer_arithmetic(self) -> None:
        tests = [
            VmTestCase(input_string='1', expected=1),
            VmTestCase('2', 2),
            VmTestCase('1 + 2', 3),
            VmTestCase('1 - 2', -1),
            VmTestCase('1 * 2', 2),
            VmTestCase('4 / 2', 2),
            VmTestCase('50 / 2 * 2 + 10 - 5', 55),
            VmTestCase('5 + 5 + 5 + 5 - 10', 10),
            VmTestCase('2 * 2 * 2 * 2 * 2', 32),
            VmTestCase('5 * 2 + 10', 20),
            VmTestCase('5 + 2 * 10', 25),
            VmTestCase('5 * (2 + 10)', 60),
            VmTestCase('-5', -5),
            VmTestCase('-10', -10),
            VmTestCase('-50 + 100 + -50', 0),
            VmTestCase('(5 + 10 * 2 + 15 / 3) * 2 + -10', 50),
        ]

        self.run_vm_tests(tests)
    
    def test_boolean_expressions(self) -> None:
        tests = [
            VmTestCase('true', True),
            VmTestCase('false', False),
            VmTestCase('1 < 2', True),
            VmTestCase('1 > 2', False),
            VmTestCase('1 < 1', False),
            VmTestCase('1 > 1', False),
            VmTestCase('1 == 1', True),
            VmTestCase('1 != 1', False),
            VmTestCase('1 == 2', False),
            VmTestCase('1 != 2', True),
            VmTestCase('true == true', True),
            VmTestCase('false == false', True),
            VmTestCase('true == false', False),
            VmTestCase('true != false', True),
            VmTestCase('false != true', True),
            VmTestCase('(1 < 2) == true', True),
            VmTestCase('(1 < 2) == false', False),
            VmTestCase('(1 > 2) == true', False),
            VmTestCase('(1 > 2) == false', True),
            VmTestCase('!true', False),
            VmTestCase('!false', True),
            VmTestCase('!5', False),
            VmTestCase('!!true', True),
            VmTestCase('!!false', False),
            VmTestCase('!!5', True),
            VmTestCase('!(if (false) { 5 })', True),
        ]

        self.run_vm_tests(tests)

    def test_string_expressions(self) -> None:
        tests = [
            VmTestCase('"monkey"', 'monkey'),
            VmTestCase('"mon" + "key"', 'monkey'),
            VmTestCase('"mon" + "key" + "banana"', 'monkeybanana'),
        ]

        self.run_vm_tests(tests)

    def test_conditionals(self) -> None:
        tests = [
            VmTestCase('if (true) { 10 }', 10),
            VmTestCase('if (true) { 10 } else { 20 }', 10),
            VmTestCase('if (false) { 10 } else { 20 }', 20),
            VmTestCase('if (1) { 10 }', 10),
            VmTestCase('if (1 < 2) { 10 }', 10),
            VmTestCase('if (1 < 2) { 10 } else { 20 }', 10),
            VmTestCase('if (1 > 2) { 10 } else { 20 }', 20),
            VmTestCase('if (1 > 2) { 10 }', None),
            VmTestCase('if (false) { 10 }', None),
            VmTestCase('if ((if (false) { 10 })) { 10 } else { 20 }', 20),
        ]

        self.run_vm_tests(tests)

    def test_global_let_statement(self) -> None:
        tests = [
            VmTestCase('let one = 1; one', 1),
            VmTestCase('let one = 1; let two = 2; one + two', 3),
            VmTestCase('let one = 1; let two = one + one; one + two', 3),
        ]

        self.run_vm_tests(tests)
    
    def test_array_literals(self) -> None:
        tests = [
            VmTestCase('[]', []),
            VmTestCase('[1, 2, 3]', [1, 2, 3]),
            VmTestCase('[1 + 2, 3 * 4, 5 + 6]', [3, 12, 11]),
        ]

        self.run_vm_tests(tests)
    
    def test_hash_literals(self) -> None:
        tests = [
            VmTestCase('{}', {}),
            VmTestCase('{1: 2, 2: 3}', {1: 2, 2: 3}),
            VmTestCase('{1 + 1: 2 * 2, 3 + 3: 4 * 4}', {2: 4, 6: 16}),
        ]

        self.run_vm_tests(tests)

    def test_index_expressions(self) -> None:
        tests = [
            VmTestCase("[1, 2, 3][1]", 2),
            VmTestCase("[1, 2, 3][0 + 2]", 3),
            VmTestCase("[[1, 1, 1]][0][0]", 1),
            VmTestCase("[][0]", None),
            VmTestCase("[1, 2, 3][99]", None),
            VmTestCase("[1][-1]", None),
            VmTestCase("{1: 1, 2: 2}[1]", 1),
            VmTestCase("{1: 1, 2: 2}[2]", 2),
            VmTestCase("{1: 1}[0]", None),
            VmTestCase("{}[0]", None),
        ]

        self.run_vm_tests(tests)
    
    def test_function_calls(self) -> None:
        tests = [
            VmTestCase("let fivePlusTen = fn() { 5 + 10 }; fivePlusTen();", 15)
        ]

        self.run_vm_tests(tests)
    
    def test_function_calls_with_bindings(self):
        tests = [
            VmTestCase(input_string='''
                        let one = fn() {let one = 1; one };
                        one();
                       ''',
                       expected=1),
            VmTestCase(input_string='''
                        let oneAndTwo = fn() { let one = 1; let two = 2; one + two; };
                        oneAndTwo();
                       ''',
                       expected=3),
            VmTestCase(input_string='''
                        let oneAndTwo = fn() { let one = 1; let two = 2; one + two; };
                        let threeAndFour = fn() { let three = 3; let four = 4; three + four; };
                        oneAndTwo() + threeAndFour();
                       ''',
                       expected=10),
            VmTestCase(input_string='''
                        let firstFoobar = fn() { let foobar = 50; foobar; };
                        let secondFoobar = fn() { let foobar = 100; foobar; };
                        firstFoobar() + secondFoobar();
                       ''',
                       expected=150),
            VmTestCase(input_string='''
                        let globalSeed = 50;
                        let minusOne = fn() {
                            let num = 1;
                            globalSeed - num;
                        }
                        let minusTwo = fn() {
                            let num = 2;
                            globalSeed - num;
                        }
                        minusOne() + minusTwo();
                       ''',
                       expected=97),
        ]

        self.run_vm_tests(tests)

    def test_function_calls_with_arguments_and_bindings(self):
        tests = [
            VmTestCase(input_string='''
                        let identity = fn(a) { a; };
                        identity(4);
                       ''',
                       expected=4),
            VmTestCase(input_string='''
                        let sum = fn(a, b) { a + b; };
                        sum(1, 2);
                       ''',
                       expected=3),
            VmTestCase(input_string='''
                        let sum = fn(a, b) {
                            let c = a + b;
                            c;
                        };
                        sum(1, 2);
                       ''',
                       expected=3),
            VmTestCase(input_string='''
                        let sum = fn(a, b) {
                            let c = a + b;
                            c;
                        };
                        sum(1, 2) + sum(3, 4);
                       ''',
                       expected=10),
            VmTestCase(input_string='''
                        let sum = fn(a, b) {
                            let c = a + b;
                            c;
                        };
                        let outer = fn() {
                            sum(1, 2) + sum(3, 4);
                        }
                        outer();
                       ''',
                       expected=10),
            VmTestCase(input_string='''
                        let globalNum = 10;
                       
                        let sum = fn(a, b) {
                            let c = a + b;
                            c + globalNum;
                        };
                       
                        let outer = fn() {
                            sum(1, 2) + sum(3, 4) + globalNum;
                        }
                       
                        outer() + globalNum;
                       ''',
                       expected=50),
        ]

        self.run_vm_tests(tests)

    def test_function_calls_with_wrong_arguments(self):
        tests = [
            VmTestCase(input_string='''fn() { 1; }(1);''',
                       expected='wrong number of arguments: want=0, got=1'),
            VmTestCase(input_string='''fn(a) { a; }();''',
                       expected='wrong number of arguments: want=1, got=0'),
            VmTestCase(input_string='''fn(a, b) { a + b; }(1);''',
                       expected='wrong number of arguments: want=2, got=1'),
        ]

        for test in tests:
            program = self.parse(test.input_string)
            compiler = Compiler()
            err = compiler.compile(program)
            if err is not None:
                self.fail(f'compiler error: {err}')
            
            vm = VirtualMachine(compiler.bytecode())
            err = vm.run()
            if err is None:
                self.fail('expected VM error but resulted in none.')
            
            if str(err) != test.expected:
                self.fail(f'wrong VM error: want={test.expected}, got={err}')

    def test_first_class_functions(self):
        tests = [
            VmTestCase(
                input_string='''
                    let returnsOneReturner = fn() {
                        let returnsOne = fn() { 1; };
                        returnsOne;
                    };
                    returnsOneReturner()();
                ''',
                expected=1,
            )
        ]

        self.run_vm_tests(tests)
    
    def test_builtin_functions(self):
        tests = [
            VmTestCase(input_string='''len("")''', expected=0),
            VmTestCase(input_string='''len("four")''', expected=4),
            VmTestCase(input_string='''len("hello world")''', expected=11),
            VmTestCase(
                input_string='''len(1)''',
                expected=ErrorObject('argument to "len" not supported, got ObjectType.INTEGER_OBJ')
            ),
            VmTestCase(
                input_string='''len("one", "two")''',
                expected=ErrorObject("wrong number of arguments. got=2, want=1")
            ),
            VmTestCase(input_string='''len([1, 2, 3])''', expected=3),
            VmTestCase(input_string='''len([])''', expected=0),
            VmTestCase(input_string='''puts("hello", "world")''', expected=NULL),
            VmTestCase(input_string='''first([1, 2, 3])''', expected=1),
            VmTestCase(input_string='''first([])''', expected=NULL),
            VmTestCase(
                input_string='''first(1)''',
                expected=ErrorObject('argument to "first" must be ARRAY, got ObjectType.INTEGER_OBJ')
            ),
            VmTestCase(input_string='''last([1, 2, 3])''', expected=3),
            VmTestCase(input_string='''last([])''', expected=NULL),
            VmTestCase(
                input_string='''last(1)''',
                expected=ErrorObject('argument to "last" must be ARRAY, got ObjectType.INTEGER_OBJ')
            ),
            VmTestCase(input_string='''rest([1, 2, 3])''', expected=[2, 3]),
            VmTestCase(input_string='''rest([])''', expected=NULL),
            VmTestCase(input_string='''push([], 1)''', expected=[1]),
            VmTestCase(
                input_string='''push(1, 1)''',
                expected=ErrorObject('argument to "push" must be ARRAY, got ObjectType.INTEGER_OBJ')
            ),
        ]

        self.run_vm_tests(tests)
    
    def test_closures(self):
        tests = [
            VmTestCase(
                input_string='''
                    let newClosure = fn(a) {
                        fn() { a; };
                    };
                    let closure = newClosure(99);
                    closure();
                    ''',
                    expected=99),
            VmTestCase(
                input_string='''
                    let newAdder = fn(a, b) {
                        fn(c) { a + b + c; };
                    };
                    let adder = newAdder(1, 2);
                    adder(8);
                    ''',
                    expected=11),
            VmTestCase(
                input_string='''
                    let newAdder = fn(a, b) {
                        let c = a + b;
                        fn(d) { c + d; };
                    };
                    let adder = newAdder(1, 2);
                    adder(8);
                    ''',
                    expected=11),
            VmTestCase(
                input_string='''
                    let newAdderOuter = fn(a, b) {
                        let c = a + b;
                        fn(d) {
                            let e = d + c;
                            fn(f) { e + f; };
                        };
                    };
                    let newAdderInner = newAdderOuter(1, 2)
                    let adder = newAdderInner(3);
                    adder(8);
                    ''',
                    expected=14),
            VmTestCase(
                input_string='''
                    let a = 1;
                    let newAdderOuter = fn(b) {
                        fn(c) {
                            fn(d) { a + b + c + d };
                        };
                    };
                    let newAdderInner = newAdderOuter(2)
                    let adder = newAdderInner(3);
                    adder(8);
                    ''',
                    expected=14),
            VmTestCase(
                input_string='''
                    let newClosure = fn(a, b) {
                        let one = fn() { a; };
                        let two = fn() { b; };
                        fn() { one() + two(); };
                    };
                    let closure = newClosure(9, 90);
                    closure();
                    ''',
                    expected=99),
        ]

        self.run_vm_tests(tests)

    def test_recursive_functions(self):
        tests = [
            VmTestCase(
                input_string='''
                    let countDown = fn(x) {
                        if (x == 0) {
                            return 0;
                        } else {
                            countDown(x - 1);
                        }
                    };
                    countDown(1);
                    ''',
                    expected=0),
            VmTestCase(
                input_string='''
                    let countDown = fn(x) {
                        if (x == 0) {
                            return 0;
                        } else {
                            countDown(x - 1);
                        }
                    };
                    let wrapper = fn() {
                        countDown(1);
                    };
                    wrapper();
                    ''',
                    expected=0),
            VmTestCase(
                input_string='''
                    let wrapper = fn() {
                        let countDown = fn(x) {
                            if (x == 0) {
                                return 0;
                            } else {
                                countDown(x - 1);
                            }
                        };
                        countDown(1);
                    };
                    wrapper();
                    ''',
                    expected=0),
        ]

        self.run_vm_tests(tests)
    
    def test_recursive_fibonacci(self):
        tests = [
            VmTestCase(
                input_string='''
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

                    fibonacci(15);
                    ''',
                    expected=610),
        ]

        self.run_vm_tests(tests)

if __name__ == '__main__':
    unittest.main()
