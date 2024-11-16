import unittest
from typing import List
from dataclasses import dataclass

from monkey import code
from monkey.object import *
from monkey.lexer import Lexer
from monkey.parser import Parser
from monkey.compiler import Compiler, Bytecode


@dataclass
class CompilerTestCase:
    input_string: str
    expected_constants:    List[int]
    expected_instructions: List[bytes]


class TestCompiler(unittest.TestCase):
    def parse(self, input_string: str) -> ast.Program:
        lexer = Lexer(input_string)
        parser = Parser(lexer)
        return parser.parse_program()
    
    def concat_instructions(self, s: List[code.Instructions]) -> code.Instructions:
        return code.Instructions(b''.join(s))

    def check_instructions(self, expected: List[code.Instructions], actual: code.Instructions):
        concatted = self.concat_instructions(expected)
        assert len(actual) == len(concatted), f'Wrong number of instructions.\nWant:\n{concatted}\nGot:\n{actual}'

        for i, ins in enumerate(concatted):
            self.assertEqual(actual[i], ins)

    def check_integer_object(self, expected: int, actual: Object):
        self.assertIsInstance(actual, IntegerObject)
        self.assertEqual(actual.value, expected)

    def check_string_object(self, expected: str, actual: Object):
        self.assertIsInstance(actual, StringObject)
        self.assertEqual(actual.value, expected)

    def check_constants(self, expected: List[int], actual: List[Object]):
        self.assertEqual(len(expected), len(actual))
        for i, constant in enumerate(expected):
            if type(constant) == int:
                self.check_integer_object(constant, actual[i])
            elif type(constant) == str:
                self.check_string_object(constant, actual[i])
            elif type(constant) == CompiledFunction:
                fn = actual[i]
                self.check_instructions(constant.instructions, fn.instructions)

    def run_compiler_tests(self, tests: List[CompilerTestCase]):
        for test in tests:
            program = self.parse(test.input_string)
            compiler = Compiler()
            compiler.compile(program)
            bytecode = compiler.bytecode()
            self.check_instructions(test.expected_instructions, bytecode.instructions)
            self.check_constants(test.expected_constants, bytecode.constants)

    def test_integer_arithmetic(self):
        tests = [
            CompilerTestCase(input_string='1; 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpPop),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 + 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpAdd),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 - 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpSub),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 * 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpMul),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='2 / 1',
                             expected_constants=[2, 1],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpDiv),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='-1',
                             expected_constants=[1],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpMinus),
                                code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)
    
    def test_boolean_expressions(self):
        tests = [
            CompilerTestCase(input_string='true',
                             expected_constants=[],
                             expected_instructions=[
                                code.make(code.Opcode.OpTrue),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='false',
                             expected_constants=[],
                             expected_instructions=[
                                code.make(code.Opcode.OpFalse),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 > 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpGreaterThan),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 < 2',
                             expected_constants=[2, 1],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpGreaterThan),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 == 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpEqual),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='1 != 2',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpNotEqual),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='true == false',
                             expected_constants=[],
                             expected_instructions=[
                                 code.make(code.Opcode.OpTrue),
                                 code.make(code.Opcode.OpFalse),
                                 code.make(code.Opcode.OpEqual),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='true != false',
                             expected_constants=[],
                             expected_instructions=[
                                 code.make(code.Opcode.OpTrue),
                                 code.make(code.Opcode.OpFalse),
                                 code.make(code.Opcode.OpNotEqual),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='!true',
                             expected_constants=[],
                             expected_instructions=[
                                 code.make(code.Opcode.OpTrue),
                                 code.make(code.Opcode.OpBang),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_conditionals(self):
        tests = [
            CompilerTestCase(input_string='if (true) { 10 }; 3333;',
                             expected_constants=[10, 3333],
                             expected_instructions=[
                                 # 0000
                                 code.make(code.Opcode.OpTrue),
                                 # 0001
                                 code.make(code.Opcode.OpJumpNotTruthy, 10),
                                 # 0004
                                 code.make(code.Opcode.OpConstant, 0),
                                 # 0007
                                 code.make(code.Opcode.OpJump, 11),
                                 # 0010
                                 code.make(code.Opcode.OpNull),
                                 # 0011
                                 code.make(code.Opcode.OpPop),
                                 # 0012
                                 code.make(code.Opcode.OpConstant, 1),
                                 # 0015
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='if (true) { 10 } else { 20 }; 3333;',
                             expected_constants=[10, 20, 3333],
                             expected_instructions=[
                                 # 0000
                                 code.make(code.Opcode.OpTrue),
                                 # 0001
                                 code.make(code.Opcode.OpJumpNotTruthy, 10),
                                 # 0004
                                 code.make(code.Opcode.OpConstant, 0),
                                 # 0007
                                 code.make(code.Opcode.OpJump, 13),
                                 # 0010
                                 code.make(code.Opcode.OpConstant, 1),
                                 # 0013
                                 code.make(code.Opcode.OpPop),
                                 # 0014
                                 code.make(code.Opcode.OpConstant, 2),
                                 # 0017
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_identifiers(self):
        tests = [
            CompilerTestCase(input_string='let one = 1; let two = 2;',
                             expected_constants=[1, 2],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpSetGlobal, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpSetGlobal, 1),
                             ]),
            CompilerTestCase(input_string='let one = 1; one;',
                             expected_constants=[1],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpSetGlobal, 0),
                                 code.make(code.Opcode.OpGetGlobal, 0),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='let one = 1; let two = one; two;',
                             expected_constants=[1],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpSetGlobal, 0),
                                 code.make(code.Opcode.OpGetGlobal, 0),
                                 code.make(code.Opcode.OpSetGlobal, 1),
                                 code.make(code.Opcode.OpGetGlobal, 1),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_string_expressions(self):
        tests = [
            CompilerTestCase(input_string='"monkey"',
                             expected_constants=["monkey"],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='"mon" + "key"',
                             expected_constants=["mon", "key"],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpAdd),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_array_literals(self):
        tests = [
            CompilerTestCase(input_string='[]',
                             expected_constants=[],
                             expected_instructions=[
                                 code.make(code.Opcode.OpArray, 0),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='[1, 2, 3]',
                             expected_constants=[1, 2, 3],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpArray, 3),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='[1 + 2, 3 - 4, 5 * 6]',
                             expected_constants=[1, 2, 3, 4, 5, 6],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpAdd),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpConstant, 3),
                                 code.make(code.Opcode.OpSub),
                                 code.make(code.Opcode.OpConstant, 4),
                                 code.make(code.Opcode.OpConstant, 5),
                                 code.make(code.Opcode.OpMul),
                                 code.make(code.Opcode.OpArray, 3),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_hash_literals(self):
        tests = [
            CompilerTestCase(input_string='{}',
                             expected_constants=[],
                             expected_instructions=[
                                 code.make(code.Opcode.OpHash, 0),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='{1: 2, 3: 4, 5: 6}',
                             expected_constants=[1, 2, 3, 4, 5, 6],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpConstant, 3),
                                 code.make(code.Opcode.OpConstant, 4),
                                 code.make(code.Opcode.OpConstant, 5),
                                 code.make(code.Opcode.OpHash, 6),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='{1: 2 + 3, 4: 5 * 6}',
                             expected_constants=[1, 2, 3, 4, 5, 6],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpAdd),
                                 code.make(code.Opcode.OpConstant, 3),
                                 code.make(code.Opcode.OpConstant, 4),
                                 code.make(code.Opcode.OpConstant, 5),
                                 code.make(code.Opcode.OpMul),
                                 code.make(code.Opcode.OpHash, 4),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_index_expressions(self):
        tests = [
            CompilerTestCase(input_string='[1, 2, 3][1 + 1]',
                             expected_constants=[1, 2, 3, 1, 1],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpArray, 3),
                                 code.make(code.Opcode.OpConstant, 3),
                                 code.make(code.Opcode.OpConstant, 4),
                                 code.make(code.Opcode.OpAdd),
                                 code.make(code.Opcode.OpIndex),
                                 code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='{1: 2}[2 - 1]',
                             expected_constants=[1, 2, 2, 1],
                             expected_instructions=[
                                 code.make(code.Opcode.OpConstant, 0),
                                 code.make(code.Opcode.OpConstant, 1),
                                 code.make(code.Opcode.OpHash, 2),
                                 code.make(code.Opcode.OpConstant, 2),
                                 code.make(code.Opcode.OpConstant, 3),
                                 code.make(code.Opcode.OpSub),
                                 code.make(code.Opcode.OpIndex),
                                 code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_compiler_scopes(self):
        compiler = Compiler()
        self.assertEqual(compiler.scope_index, 0)
        global_table = compiler.symbol_table
        compiler.emit(code.Opcode.OpMul)

        compiler.enter_scope()
        self.assertEqual(compiler.scope_index, 1)
        compiler.emit(code.Opcode.OpSub)
        self.assertEqual(len(compiler.current_scope.instructions), 1)
        last = compiler.current_scope.last_instruction
        self.assertEqual(last.opcode, code.Opcode.OpSub)
        self.assertEqual(compiler.symbol_table.outer, global_table)

        compiler.leave_scope()
        self.assertEqual(compiler.scope_index, 0)
        self.assertEqual(compiler.symbol_table, global_table)
        self.assertIsNone(compiler.symbol_table.outer, global_table)
        compiler.emit(code.Opcode.OpAdd)
        self.assertEqual(len(compiler.current_scope.instructions), 2)
        last = compiler.current_scope.last_instruction
        self.assertEqual(last.opcode, code.Opcode.OpAdd)
        previous = compiler.current_scope.previous_instruction
        self.assertEqual(previous.opcode, code.Opcode.OpMul)

    def test_functions(self):
        tests = [
            CompilerTestCase(input_string='fn() { return 5 + 10 }',
                             expected_constants=[
                                5,
                                10,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpConstant, 1),
                                    code.make(code.Opcode.OpAdd),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 2, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='fn() { 5 + 10 }',
                             expected_constants=[
                                5,
                                10,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpConstant, 1),
                                    code.make(code.Opcode.OpAdd),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 2, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='fn() { 1; 2 }',
                             expected_constants=[
                                1,
                                2,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpPop),
                                    code.make(code.Opcode.OpConstant, 1),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 2, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='fn() { }',
                             expected_constants=[
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpReturn),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 0, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)
    
    def test_function_calls(self):
        tests = [
            CompilerTestCase(input_string='fn() { 24 }();',
                             expected_constants=[
                                24,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 1, 0),
                                code.make(code.Opcode.OpCall, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='let noArg = fn() { 24 }; noArg();',
                             expected_constants=[
                                24,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 1, 0),
                                code.make(code.Opcode.OpSetGlobal, 0),
                                code.make(code.Opcode.OpGetGlobal, 0),
                                code.make(code.Opcode.OpCall, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='let oneArg = fn(a) { a }; oneArg(24);',
                             expected_constants=[
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpGetLocal, 0),
                                    code.make(code.Opcode.OpReturnValue),
                                ]),
                                24,
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 0, 0),
                                code.make(code.Opcode.OpSetGlobal, 0),
                                code.make(code.Opcode.OpGetGlobal, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpCall, 1),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='let manyArgs = fn(a, b, c) { a; b; c }; manyArgs(24, 25, 26);',
                             expected_constants=[
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpGetLocal, 0),
                                    code.make(code.Opcode.OpPop),
                                    code.make(code.Opcode.OpGetLocal, 1),
                                    code.make(code.Opcode.OpPop),
                                    code.make(code.Opcode.OpGetLocal, 2),
                                    code.make(code.Opcode.OpReturnValue),
                                ]),
                                24,
                                25,
                                26
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 0, 0),
                                code.make(code.Opcode.OpSetGlobal, 0),
                                code.make(code.Opcode.OpGetGlobal, 0),
                                code.make(code.Opcode.OpConstant, 1),
                                code.make(code.Opcode.OpConstant, 2),
                                code.make(code.Opcode.OpConstant, 3),
                                code.make(code.Opcode.OpCall, 3),
                                code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_let_statement_scopes(self):
        tests = [
            CompilerTestCase(input_string='''
                                let num = 55;
                                fn() { num }
                                ''',
                             expected_constants=[
                                55,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpGetGlobal, 0),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpSetGlobal, 0),
                                code.make(code.Opcode.OpClosure, 1, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='''
                                fn() {
                                    let num = 55;
                                    num
                                }
                                ''',
                             expected_constants=[
                                55,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpSetLocal, 0),
                                    code.make(code.Opcode.OpGetLocal, 0),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 1, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='''
                                fn() {
                                    let a = 55;
                                    let b = 77;
                                    a + b
                                }
                                ''',
                             expected_constants=[
                                55,
                                77,
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpConstant, 0),
                                    code.make(code.Opcode.OpSetLocal, 0),
                                    code.make(code.Opcode.OpConstant, 1),
                                    code.make(code.Opcode.OpSetLocal, 1),
                                    code.make(code.Opcode.OpGetLocal, 0),
                                    code.make(code.Opcode.OpGetLocal, 1),
                                    code.make(code.Opcode.OpAdd),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 2, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

    def test_builtins(self):
        tests = [
            CompilerTestCase(input_string='''
                                len([]);
                                push([], 1);
                             ''',
                             expected_constants=[1],
                             expected_instructions=[
                                code.make(code.Opcode.OpGetBuiltin, 0),
                                code.make(code.Opcode.OpArray, 0),
                                code.make(code.Opcode.OpCall, 1),
                                code.make(code.Opcode.OpPop),
                                code.make(code.Opcode.OpGetBuiltin, 5),
                                code.make(code.Opcode.OpArray, 0),
                                code.make(code.Opcode.OpConstant, 0),
                                code.make(code.Opcode.OpCall, 2),
                                code.make(code.Opcode.OpPop),
                             ]),
            CompilerTestCase(input_string='''fn() { len([]) }''',
                             expected_constants=[
                                CompiledFunction(instructions=[
                                    code.make(code.Opcode.OpGetBuiltin, 0),
                                    code.make(code.Opcode.OpArray, 0),
                                    code.make(code.Opcode.OpCall, 1),
                                    code.make(code.Opcode.OpReturnValue),
                                ])
                             ],
                             expected_instructions=[
                                code.make(code.Opcode.OpClosure, 0, 0),
                                code.make(code.Opcode.OpPop),
                             ]),
        ]

        self.run_compiler_tests(tests)

if __name__ == '__main__':
    unittest.main()
