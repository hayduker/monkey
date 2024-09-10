import unittest
from typing import List
from dataclasses import dataclass

from monkey import code


class TestBytecode(unittest.TestCase):
    def test_make(self):
        @dataclass
        class Test:
            op: code.Opcode
            operands: List[int]
            expected: bytes
        
        tests = [
            Test(code.Opcode.OpConstant, [65534], code.Opcode.OpConstant.value + b'\xff\xfe'),
            Test(code.Opcode.OpAdd,      [],      code.Opcode.OpAdd.value),
        ]

        for test in tests:
            instruction = code.make(test.op, *test.operands)

            self.assertEqual(len(instruction), len(test.expected))
            for i in range(len(test.expected)):
                self.assertEqual(instruction[i], test.expected[i])

    def test_read_operands(self):
        @dataclass
        class Test:
            op: code.Opcode
            operands: List[int]
            bytes_read: List[int]
        
        tests = [
            Test(code.Opcode.OpConstant, [65535], 2),
        ]

        for test in tests:
            instruction = code.make(test.op, *test.operands)
            defn = code.definitions.get(test.op, None)
            self.assertIsNotNone(defn)

            operands_read, n = code.read_operands(defn, instruction[1:])
            self.assertEqual(n, test.bytes_read)
            for i, want in enumerate(test.operands):
                self.assertEqual(operands_read[i], want)

    def test_instructions_string(self):
        instructions = [
            code.make(code.Opcode.OpAdd),
            code.make(code.Opcode.OpConstant, 2),
            code.make(code.Opcode.OpConstant, 65535)
        ]

        expected = '0000 OpAdd\n0001 OpConstant 2\n0004 OpConstant 65535\n'

        concatted = code.Instructions(b''.join(instructions))
        self.assertEqual(str(concatted), expected)


if __name__ == '__main__':
    unittest.main()