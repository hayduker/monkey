import unittest
import builtins
from dataclasses import dataclass
from typing import Any

from monkey.lexer import Lexer
from monkey import myast as ast
from monkey.parser import Parser

class ParserTestCase(unittest.TestCase):

    ##################
    # Helper methods #
    ##################

    def check_parse_errors(self, parser):
        errors = parser.get_errors()
        
        if len(errors) == 0:
            return
        
        print(f'\nParser has {len(errors)} errors.')
        for msg in errors:
            print(f'Parser error: {msg}')

        self.fail('Failing from parser errors.')

    def check_integer_literal(self, literal, expected_value):
        self.assertEqual(type(literal),           ast.IntegerLiteral)
        self.assertEqual(literal.value,           expected_value)
        self.assertEqual(literal.token_literal(), str(expected_value))
    
    def check_string_literal(self, literal, expected_value):
        self.assertEqual(type(literal),           ast.StringLiteral)
        self.assertEqual(literal.value,           expected_value)
        self.assertEqual(literal.token_literal(), str(expected_value))
    
    def check_identifier(self, expression, expected_value):
        self.assertEqual(type(expression),           ast.Identifier)
        self.assertEqual(expression.value,           expected_value)
        self.assertEqual(expression.token_literal(), str(expected_value))

    def check_boolean_literal(self, expression, expected_value):
        self.assertEqual(type(expression),           ast.Boolean)
        self.assertEqual(expression.value,           expected_value)
        self.assertEqual(expression.token_literal(), str(expected_value).lower()) 

    def check_literal_expression(self, expression, expected_value):
        match type(expected_value):
            case builtins.int:
                self.check_integer_literal(expression, expected_value)
            case builtins.str:
                self.check_identifier(expression, expected_value)
            case builtins.bool:
                self.check_boolean_literal(expression, expected_value)
            case _:
                self.fail(f'We do not handle type {type(expected_value)} in check_literal_expression')

    def check_infix_expression(self, expression, left, operator, right):
        self.assertEqual(type(expression), ast.InfixExpression)        
        self.check_literal_expression(expression.left, left)
        self.assertEqual(expression.operator, operator)
        self.check_literal_expression(expression.right, right)

    ##########################
    # Testing let statements #
    ##########################

    def check_let_statement(self, statement, expected_id):
        self.assertEqual(statement.token_literal(),      'let')
        self.assertEqual(type(statement),                ast.LetStatement)
        self.assertEqual(statement.name.value,           expected_id)
        self.assertEqual(statement.name.token_literal(), expected_id)        

    def test_let_statements(self):
        @dataclass
        class Test:
            input_string: str
            expected_identifier: str
            expected_value: Any

        tests = [
            Test('let x = 5;',      'x',      5),
            Test('let y = true;',   'y',      True),
            Test('let foobar = y;', 'foobar', 'y')
        ]

        for test in tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.statements), 1)

            stmt = program.statements[0]
            self.check_let_statement(stmt, test.expected_identifier)

            val = stmt.value
            self.check_literal_expression(val, test.expected_value)

    #############################
    # Testing return statements #
    #############################

    def test_return_statements(self):
        @dataclass
        class Test:
            input_string: str
            expected_value: Any

        tests = [
            Test('return 5;',      5),
            Test('return true;',   True),
            Test('return foobar;', 'foobar')
        ]

        for test in tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.statements), 1)

            value = program.statements[0].return_value
            self.check_literal_expression(value, test.expected_value)

    ##################################
    # Testing identifier expressions #
    ##################################

    def test_identifier_expression(self):
        input_string = 'foobar;'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)
        self.check_identifier(stmt.expression, 'foobar')

    ########################################
    # Testing interger literal expressions #
    ########################################

    def test_integer_literal_expression(self):
        input_string = '5;'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)
        self.check_integer_literal(stmt.expression, 5)

    ######################################
    # Testing string literal expressions #
    ######################################

    def test_string_literal_expression(self):
        input_string = '"foobar";'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)
        self.check_string_literal(stmt.expression, "foobar")

    #######################################
    # Testing boolean literal expressions #
    #######################################

    def test_boolean_expression(self):
        @dataclass
        class Test:
            input_string: str
            expected_boolean: bool
        
        tests = [
            Test('true;', True),
            Test('false;', False)
        ]

        for test in tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.statements), 1)

            stmt = program.statements[0]
            self.assertEqual(type(stmt), ast.ExpressionStatement)
            self.check_boolean_literal(stmt.expression, test.expected_boolean)

    ###################################
    # Testing conditional expressions #
    ###################################

    def test_if_expression(self):
        input_string = 'if (x < y) { x }'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        expr = program.statements[0].expression
        self.assertEqual(type(expr), ast.IfExpression)
        self.check_infix_expression(expr.condition, 'x', '<', 'y')

        consequences = expr.consequence
        self.assertEqual(type(consequences), ast.BlockStatement)
        self.assertEqual(len(consequences.statements), 1)

        consequence = consequences.statements[0]
        self.assertEqual(type(consequence), ast.ExpressionStatement)
        self.check_identifier(consequence.expression, 'x')

        self.assertIsNone(expr.alternative)

    def test_if_else_expression(self):
        input_string = 'if (x < y) { x } else { y }'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        expr = program.statements[0].expression
        self.assertEqual(type(expr), ast.IfExpression)
        self.check_infix_expression(expr.condition, 'x', '<', 'y')

        consequences = expr.consequence
        self.assertEqual(type(consequences), ast.BlockStatement)
        self.assertEqual(len(consequences.statements), 1)

        consequence = consequences.statements[0]
        self.assertEqual(type(consequence), ast.ExpressionStatement)
        self.check_identifier(consequence.expression, 'x')

        alternatives = expr.alternative
        self.assertEqual(type(alternatives), ast.BlockStatement)
        self.assertEqual(len(alternatives.statements), 1)

        alternative = alternatives.statements[0]
        self.assertEqual(type(alternative), ast.ExpressionStatement)
        self.check_identifier(alternative.expression, 'y')

    ################################
    # Testing function expressions #
    ################################

    def test_function_literal_parsing(self):
        input_string = 'fn(x, y) { x + y; }'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertTrue(type(stmt), ast.ExpressionStatement)

        function = stmt.expression
        self.assertTrue(type(function), ast.FunctionLiteral)
        
        self.assertTrue(len(function.parameters), 2)
        self.check_literal_expression(function.parameters[0], 'x')
        self.check_literal_expression(function.parameters[1], 'y')

        self.assertTrue(len(function.body.statements), 1)
        body_stmt = function.body.statements[0]
        self.assertTrue(type(body_stmt), ast.ExpressionStatement)
        self.check_infix_expression(body_stmt.expression, 'x', '+', 'y')
    
    def test_function_literal_with_name(self):
        input_string = 'let myFunction = fn() { };'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertTrue(type(stmt), ast.LetStatement)

        function = stmt.value
        self.assertTrue(type(function), ast.FunctionLiteral)
        self.assertEqual(function.name, 'myFunction')

    def test_function_parameters_parsing(self):
        @dataclass
        class Test:
            input_string: str
            expected_params: list[str]
        
        tests = [
            Test('fn() {};', []),
            Test('fn(x) {};', ['x']),
            Test('fn(x, y, z) {};', ['x', 'y', 'z'])
        ]

        for test in tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)

            stmt = program.statements[0]
            function = stmt.expression

            self.assertEqual(len(function.parameters), len(test.expected_params))
            for i, identifier in enumerate(test.expected_params):
                self.check_literal_expression(function.parameters[i], identifier)

    def test_call_expression_parsing(self):
        input_string = 'add(1, 2 * 3, 4 + 5);'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertTrue(type(stmt), ast.ExpressionStatement)

        call_expression = stmt.expression
        self.assertEqual(type(call_expression), ast.CallExpression)
        self.check_identifier(call_expression.function, 'add')
        
        self.assertEqual(len(call_expression.arguments), 3)
        self.check_literal_expression(call_expression.arguments[0], 1)
        self.check_infix_expression(call_expression.arguments[1], 2, '*', 3)
        self.check_infix_expression(call_expression.arguments[2], 4, '+', 5)

    ##########################
    # Test array expressions #
    ##########################

    def test_array_literal_expressions(self):
        input_string = '[1, 2 * 2, 3 + 3]'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)

        array = stmt.expression
        self.assertEqual(type(array), ast.ArrayLiteral)
        self.assertEqual(len(array.elements), 3)
        self.check_integer_literal(array.elements[0], 1)
        self.check_infix_expression(array.elements[1], 2, '*', 2)
        self.check_infix_expression(array.elements[2], 3, '+', 3)

    def test_parsing_index_expressions(self):
        input_string = 'myArray[1 + 1]'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)

        index_exp = stmt.expression
        self.assertEqual(type(index_exp), ast.IndexExpression)
        self.check_identifier(index_exp.left, 'myArray')
        self.check_infix_expression(index_exp.index, 1, '+', 1)

    #########################
    # Test hash expressions #
    #########################

    def test_hash_literal_expressions(self):
        input_string = '{"one": 1, "two": 2, "three": 3}'
        expected = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4
        }

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)

        hush = stmt.expression
        self.assertEqual(type(hush), ast.HashLiteral)
        self.assertEqual(len(hush.pairs), 3)

        for key, value in hush.pairs.items():
            self.assertTrue(type(key), ast.StringLiteral)

            expected_value = expected[str(key)]
            self.check_integer_literal(value, expected_value)

    def test_parsing_empty_hash_literal(self):
        input_string = '{}'

        lexer = Lexer(input_string)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.check_parse_errors(parser)
        self.assertIsNotNone(program)
        self.assertEqual(len(program.statements), 1)

        stmt = program.statements[0]
        self.assertEqual(type(stmt), ast.ExpressionStatement)

        hush = stmt.expression
        self.assertEqual(type(hush), ast.HashLiteral)
        self.assertEqual(len(hush.pairs), 0)

    ##############################
    # Testing prefix expressions #
    ##############################

    def test_parsing_prefix_expressions(self):
        @dataclass
        class PrefixTest:
            input_string: str
            operator: str
            right_value: Any

        prefix_tests = [
            PrefixTest('!5',      '!', 5),
            PrefixTest('-15',     '-', 15),
            PrefixTest('!true;',  '!', True),
            PrefixTest('!false;', '!', False),
        ]

        for test in prefix_tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.statements), 1)

            stmt = program.statements[0]
            self.assertEqual(type(stmt), ast.ExpressionStatement)

            exp = stmt.expression
            self.assertEqual(type(exp), ast.PrefixExpression)
            self.assertEqual(exp.operator, test.operator)
            self.check_literal_expression(exp.right, test.right_value)

    #############################
    # Testing infix expressions #
    #############################

    def test_parsing_infix_expressions(self):
        @dataclass
        class InfixTest:
            input_string: str
            left_value: Any
            operator: str
            right_value: Any

        infix_tests = [
            InfixTest('5 + 5;',         5,    '+',   5),
            InfixTest('5 - 5;',         5,    '-',   5),
            InfixTest('5 * 5;',         5,    '*',   5),
            InfixTest('5 / 5;',         5,    '/',   5),
            InfixTest('5 > 5;',         5,    '>',   5),
            InfixTest('5 < 5;',         5,    '<',   5),
            InfixTest('5 == 5;',        5,    '==',  5),
            InfixTest('5 != 5;',        5,    '!=',  5),
            InfixTest('true == true',   True, '==',  True),
            InfixTest('true != false',  True, '!=',  False),
            InfixTest('false == false', False, '==', False),
        ]

        for test in infix_tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)
            self.assertEqual(len(program.statements), 1)

            stmt = program.statements[0]
            self.assertEqual(type(stmt), ast.ExpressionStatement)
            self.check_infix_expression(stmt.expression, test.left_value, test.operator, test.right_value)

    def test_operator_precedence_parsing(self):
        @dataclass
        class Test:
            input_string: str
            expected: str

        tests = [
            Test('-a * b',                             '((-a) * b)'),
            Test('!-a',                                '(!(-a))'),
            Test('a + b + c',                          '((a + b) + c)'),
            Test('a + b - c',                          '((a + b) - c)'),
            Test('a * b * c',                          '((a * b) * c)'),
            Test('a * b / c',                          '((a * b) / c)'),
            Test('a + b / c',                          '(a + (b / c))'),
            Test('a + b * c + d / e - f',              '(((a + (b * c)) + (d / e)) - f)'),
            Test('3 + 4; -5 * 5',                      '(3 + 4)((-5) * 5)'),
            Test('5 > 4 == 3 < 4',                     '((5 > 4) == (3 < 4))'),
            Test('5 < 4 != 3 > 4',                     '((5 < 4) != (3 > 4))'),
            Test('3 + 4 * 5 == 3 * 1 + 4 * 5',         '((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))'),
            Test('3 + 4 * 5 == 3 * 1 + 4 * 5',         '((3 + (4 * 5)) == ((3 * 1) + (4 * 5)))'),
            Test('true',                               'True'),
            Test('false',                              'False'),
            Test('3 > 5 == false',                     '((3 > 5) == False)'),
            Test('3 < 5 == true',                      '((3 < 5) == True)'),
            Test('1 + (2 + 3) + 4',                    '((1 + (2 + 3)) + 4)'),
            Test('(5 + 5) * 2',                        '((5 + 5) * 2)'),
            Test('2 / (5 + 5)',                        '(2 / (5 + 5))'),
            Test('-(5 + 5)',                           '(-(5 + 5))'),
            Test('!(true == true)',                    '(!(True == True))'),
            Test('a * [1, 2, 3, 4][b * c] * d',        '((a * ([1, 2, 3, 4][(b * c)])) * d)'),
            Test('add(a * b[2], b[1], 2 * [1, 2][1])', 'add((a * (b[2])), (b[1]), (2 * ([1, 2][1])))'),
        ]

        for test in tests:
            lexer = Lexer(test.input_string)
            parser = Parser(lexer)
            program = parser.parse_program()

            self.check_parse_errors(parser)
            self.assertIsNotNone(program)      

            actual = str(program)
            self.assertEqual(actual, test.expected)



if __name__ == '__main__':
    unittest.main(verbosity=2)