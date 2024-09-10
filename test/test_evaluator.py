import unittest
from dataclasses import dataclass
from typing import Any

from monkey.lexer import Lexer
from monkey.parser import Parser
from monkey.evaluator import Evaluator
from monkey.object import *

class EvaluatorTestCase(unittest.TestCase):

    ##################
    # Helper methods #
    ##################

    def run_evaluate(self, input_string):
        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()
        env = Environment()
        return Evaluator().evaluate(program, env)

    def check_integer_object(self, obj: Object, expected: int):
        self.assertEqual(type(obj), IntegerObject)
        self.assertEqual(obj.value, expected)

    def check_string_object(self, obj: Object, expected: str):
        self.assertEqual(type(obj), StringObject)
        self.assertEqual(obj.value, expected)

    def check_boolean_object(self, obj: Object, expected: bool):
        self.assertEqual(type(obj), BooleanObject)
        self.assertEqual(obj.value, expected)

    def check_null_object(self, obj: Object):
        self.assertEqual(obj, NULL)

    ############################
    # Test integer expressions #
    ############################

    def test_eval_integer_expression(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: int

        tests = [
            Test('5',   5),
            Test('10',  10),
            Test('-5',  -5),
            Test('-10', -10),
            Test('5 + 5 + 5 + 5 - 10', 10),
            Test('2 * 2 * 2 * 2 * 2', 32),
            Test('-50 + 100 + -50', 0),
            Test('5 * 2 + 10', 20),
            Test('5 + 2 * 10', 25),
            Test('20 + 2 * -10', 0),
            Test('50 / 2 * 2 + 10', 60),
            Test('2 * (5 + 10)', 30),
            Test('3 * 3 * 3 + 10', 37),
            Test('3 * (3 * 3) + 10', 37),
            Test('(5 + 10 * 2 + 15 / 3) * 2 + -10', 50),

        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.check_integer_object(evaluated, test.expected_value)

    ###########################
    # Test string expressions #
    ###########################

    def test_eval_string_expression(self):
        input_string = '"foobar"'

        evaluated = self.run_evaluate(input_string)
        self.check_string_object(evaluated, 'foobar')

    def test_string_concatenation(self):
        input_string = '"Hello" + " " + "World!"'

        evaluated = self.run_evaluate(input_string)
        self.check_string_object(evaluated, 'Hello World!')

    ############################
    # Test boolean expressions #
    ############################

    def test_eval_boolean_expression(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: bool

        tests = [
            Test('true', True),
            Test('false', False),
            Test('1 < 2', True),
            Test('1 > 2', False),
            Test('1 < 1', False),
            Test('1 > 1', False),
            Test('1 == 1', True),
            Test('1 != 1', False),
            Test('1 == 2', False),
            Test('1 != 2', True),
            Test('true == true', True),
            Test('false == false', True),
            Test('true == false', False),
            Test('true != false', True),
            Test('false != true', True),
            Test('(1 < 2) == true', True),
            Test('(1 < 2) == false', False),
            Test('(1 > 2) == true', False),
            Test('(1 > 2) == false', True),
        ]
      

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.check_boolean_object(evaluated, test.expected_value)

    ##########################
    # Test prefix  operators #
    ##########################

    def test_bang_operator(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: bool

        tests = [
            Test('!true',   False),
            Test('!false',  True),
            Test('!5',      False),
            Test('!!true',  True),
            Test('!!false', False),
            Test('!!5',     True)
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.check_boolean_object(evaluated, test.expected_value)

    ##############################
    # Test condition expressions #
    ##############################

    def test_if_else_expressions(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: Any

        tests = [
            Test('if (true) { 10 }', 10),
            Test('if (false) { 11 }', None),
            Test('if (1) { 10 }', 10),
            Test('if (1 < 2) { 10 }', 10),
            Test('if (1 > 2) { 13 }', None),
            Test('if (1 > 2) { 10 } else { 20 }', 20),
            Test('if (1 < 2) { 10 } else { 20 }', 10),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            if test.expected_value is None:
                self.check_null_object(evaluated)
            else:
                self.check_integer_object(evaluated, test.expected_value)

    ##########################
    # Test return statements #
    ##########################

    def test_return_statements(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: int
        
        tests = [
            Test('return 10;', 10),
            Test('return 10; 9;', 10),
            Test('return 2 * 5; 9;', 10),
            Test('9; return 2 * 5; 9;', 10),
            Test('''
                if (10 > 1) {
                    if (10 > 1) {
                        return 10;
                    }
                    return 1;
                }
                ''', 10),
            Test('''
                let f = fn(x) {
                return x;
                x + 10;
                };
                f(10);
                ''', 10),
            Test('''
                let f = fn(x) {
                let result = x + 10;
                return result;
                return 10;
                };
                f(10);
                ''', 20),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.check_integer_object(evaluated, test.expected_value)

    #######################
    # Test let statements #
    #######################

    def test_let_statements(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: int

        tests = [
            Test('let a = 5; a;', 5),
            Test('let a = 5 * 5; a;', 25),
            Test('let a = 5; let b = a; b;', 5),
            Test('let a = 5; let b = a; let c = a + b + 5; c;', 15),
        ]

        for test in tests:
            self.check_integer_object(self.run_evaluate(test.input_string), test.expected_value)

    ############################################
    # Test function definition and application #
    ############################################

    def test_function_object(self):
        input_string = 'fn(x) { x + 2; };'
        fn = self.run_evaluate(input_string)
        
        self.assertEqual(type(fn), FunctionObject)
        self.assertEqual(len(fn.parameters), 1)
        self.assertEqual(str(fn.parameters[0]), 'x')
        self.assertEqual(str(fn.body), '(x + 2)')

    def test_function_application(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: int

        tests = [
            Test('let identity = fn(x) { x; }; identity(5);', 5),
            Test('let identity = fn(x) { return x; }; identity(5);', 5),
            Test('let double = fn(x) { x * 2; }; double(5);', 10),
            Test('let add = fn(x, y) { x + y; }; add(5, 5);', 10),
            Test('let add = fn(x, y) { x + y; }; add(5 + 5, add(5, 5));', 20),
            Test('fn(x) { x; }(5)', 5),
        ]

        for test in tests:
            self.check_integer_object(self.run_evaluate(test.input_string), test.expected_value)
    
    def test_closures(self):
        input_string = '''
            let newAdder = fn(x) {
                fn(y) { x + y };
            }

            let addTwo = newAdder(2);
            addTwo(2);
        '''

        self.check_integer_object(self.run_evaluate(input_string), 4)

    ######################################
    # Test array definition and indexing #
    ######################################

    def test_array_literal(self):
        input_string = '[1, 2 * 2, 3 + 3]'

        array = self.run_evaluate(input_string)
        self.assertEqual(type(array), ArrayObject)
        self.assertEqual(len(array.elements), 3)
        self.check_integer_object(array.elements[0], 1)
        self.check_integer_object(array.elements[1], 4)
        self.check_integer_object(array.elements[2], 6)
    
    def test_array_index_expressions(self):
        @dataclass
        class Test:
            input_string: str
            expected: Any
        
        tests = [
            Test('[1, 2, 3][0]', 1),
            Test('[1, 2, 3][1]', 2),
            Test('[1, 2, 3][2]', 3),
            Test('let i = 0; [1][i];', 1),
            Test('[1, 2, 3][1 + 1];', 3),
            Test('let myArray = [1, 2, 3]; myArray[2];', 3),
            Test('let myArray = [1, 2, 3]; myArray[0] + myArray[1] + myArray[2];', 6),
            Test('let myArray = [1, 2, 3]; let i = myArray[0]; myArray[i]', 2),
            Test('[1, 2, 3][3]', None),
            Test('[1, 2, 3][-1]', None),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            if type(test.expected) is int:
                self.check_integer_object(evaluated, test.expected)
            else:
                self.check_null_object(evaluated)

    #####################################
    # Test hash definition and indexing #
    #####################################

    def test_hash_literals(self):
        input_string = '''
        let two = "two";
        {
            "one": 10 - 9,
            two: 1 + 1,
            "thr" + "ee": 6 / 2,
            4: 4,
            true: 5,
            false: 6
        }
        '''
        expected = {
            StringObject(value="one"): 1,
            StringObject(value="two"): 2,
            StringObject(value="three"): 3,
            IntegerObject(value=4): 4,
            TRUE: 5,
            FALSE: 6
        }

        evaluated = self.run_evaluate(input_string)
        self.assertTrue(type(evaluated), HashObject)
        self.assertTrue(len(evaluated.pairs), len(expected))
        
        for expected_key, expected_value in expected.items():
            value = evaluated.pairs[expected_key]
            self.check_integer_object(value, expected_value)

    def test_hash_index_expresions(self):
        @dataclass
        class Test:
            input_string: str
            expected: Any
        
        tests = [
            Test('{"foo": 5}["foo"]', 5),
            Test('{"foo": 5}["bar"]', None),
            Test('let key = "foo"; {"foo": 5}[key]', 5),
            Test('{}["foo"]', None),
            Test('{5: 5}[5]', 5),
            Test('{true: 5}[true]', 5),
            Test('{false: 5}[false]', 5),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            if type(test.expected) is int:
                self.check_integer_object(evaluated, test.expected)
            else:
                self.check_null_object(evaluated)


    ##########################
    # Test builtin functions #
    ##########################

    def test_builtin_functions(self):
        @dataclass
        class Test:
            input_string: str
            expected: Any

        tests = [
            Test('len("")', 0),
            Test('len("four")', 4),
            Test('len("hello world")', 11),
            Test('len(1)', 'argument to "len" not supported, got ObjectType.INTEGER_OBJ'),
            Test('len("one", "two")', 'wrong number of arguments. got=2, want=1'),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            if type(test.expected) is int:
                self.check_integer_object(evaluated, test.expected)
            elif type(test.expected) is str:
                self.assertEqual(evaluated.message, test.expected)
            else:
                self.fail(f'failed with evaluated: {evaluated}')

    ###############
    # Test macros #
    ###############

    def test_quote(self):
        @dataclass
        class Test:
            input_string: str
            expected: str
        
        tests = [
            Test('quote(5)', '5'),
            Test('quote(5 + 8)', '(5 + 8)'),
            Test('quote(foobar)', 'foobar'),
            Test('quote(foobar + barfoo)', '(foobar + barfoo)'),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.assertEqual(type(evaluated), QuoteObject)
            self.assertIsNotNone(evaluated.node)
            self.assertEqual(str(evaluated.node), test.expected)
    
    def test_unquote(self):
        @dataclass
        class Test:
            input_string: str
            expected: str
        
        tests = [
            Test('quote(unquote(4))', '4'),
            Test('quote(unquote(4 + 4))', '8'),
            Test('quote(8 + unquote(4 + 4))', '(8 + 8)'),
            Test('quote(unquote(4 + 4) + 8)', '(8 + 8)'),
            Test('let foobar = 8; quote(foobar)', 'foobar'),
            Test('let foobar = 8; quote(unquote(foobar))', '8'),
            Test('quote(unquote(true))', 'true'),
            Test('quote(unquote(true == false))', 'false'),
            Test('quote(unquote(quote(4 + 4)))', '(4 + 4)'),
            Test('''let quotedInfixExpression = quote(4 + 4);
                    quote(unquote(4 + 4) + unquote(quotedInfixExpression))''',
                 '(8 + (4 + 4))')
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.assertEqual(type(evaluated), QuoteObject)
            self.assertIsNotNone(evaluated.node)
            self.assertEqual(str(evaluated.node), test.expected)

    #######################
    # Test error handling #
    #######################

    def test_error_handling(self):
        @dataclass
        class Test:
            input_string: str
            expected_message: str

        tests = [
            Test('5 + true;',                     'type mismatch: INTEGER + BOOLEAN'),
            Test('5 + true; 5;',                  'type mismatch: INTEGER + BOOLEAN'),
            Test('-true',                         'unknown operator: -BOOLEAN'),
            Test('true + false;',                 'unknown operator: BOOLEAN + BOOLEAN'),
            Test('true + false + true + false;',  'unknown operator: BOOLEAN + BOOLEAN'),
            Test('5; true + false; 5',            'unknown operator: BOOLEAN + BOOLEAN'),
            Test('if (10 > 1) { true + false; }', 'unknown operator: BOOLEAN + BOOLEAN'),
            Test('''
                if (10 > 1) {
                    if (10 > 1) {
                        return true + false;
                    }

                return 1;
                }
                ''',                              'unknown operator: BOOLEAN + BOOLEAN'),
            Test('foobar',                        'identifier not found: foobar'),
        ]

        for test in tests:
            evaluated = self.run_evaluate(test.input_string)
            self.assertEqual(type(evaluated), ErrorObject)
            self.assertEqual(evaluated.message, test.expected_message)

if __name__ == '__main__':
    unittest.main(verbosity=2)