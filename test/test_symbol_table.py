import unittest
from dataclasses import dataclass
from typing import List

from monkey.symbol_table import Symbol, SymbolTable, GlobalScope, LocalScope

class TestSymbolTable(unittest.TestCase):
    def test_define(self):
        expected = {
            'a': Symbol(name='a', scope=GlobalScope, index=0),
            'b': Symbol(name='b', scope=GlobalScope, index=1),
            'c': Symbol(name='c', scope=LocalScope, index=0),
            'd': Symbol(name='d', scope=LocalScope, index=1),
            'e': Symbol(name='e', scope=LocalScope, index=0),
            'f': Symbol(name='f', scope=LocalScope, index=1),
        }

        global_table = SymbolTable()

        a = global_table.define('a')
        self.assertEqual(a, expected['a'])

        b = global_table.define('b')
        self.assertEqual(b, expected['b'])

        first_local_table = SymbolTable(outer=global_table)

        c = first_local_table.define('c')
        self.assertEqual(c, expected['c'])

        d = first_local_table.define('d')
        self.assertEqual(d, expected['d'])

        second_local_table = SymbolTable(outer=first_local_table)

        e = second_local_table.define('e')
        self.assertEqual(e, expected['e'])

        f = second_local_table.define('f')
        self.assertEqual(f, expected['f'])

    def test_resolve(self):
        global_table = SymbolTable()
        a = global_table.define('a')
        b = global_table.define('b')

        expected = [
            Symbol(name='a', scope=GlobalScope, index=0),
            Symbol(name='b', scope=GlobalScope, index=1),
        ]

        for sym in expected:
            result = global_table.resolve(sym.name)           
            self.assertIsNotNone(result, f'symbol {sym.name} not resolvable')
            self.assertEqual(result, sym, f'expected {sym.name} to resolve to {sym} but got {result}')

    def test_resolve_local(self):
        global_table = SymbolTable()
        global_table.define('a')
        global_table.define('b')

        local_table = SymbolTable(outer=global_table)
        local_table.define('c')
        local_table.define('d')

        expected = [
            Symbol(name='a', scope=GlobalScope, index=0),
            Symbol(name='b', scope=GlobalScope, index=1),
            Symbol(name='c', scope=LocalScope, index=0),
            Symbol(name='d', scope=LocalScope, index=1),
        ]

        for sym in expected:
            result = local_table.resolve(sym.name)
            self.assertIsNotNone(result, f'name {sym.name} not resolvable')
            self.assertEqual(result, sym, f'expected {sym.name} to resolve to {sym} but got {result}')

    def test_resolve_nested_local(self):
        global_table = SymbolTable()
        global_table.define('a')
        global_table.define('b')

        first_local_table = SymbolTable(outer=global_table)
        first_local_table.define('c')
        first_local_table.define('d')

        second_local_table = SymbolTable(outer=first_local_table)
        second_local_table.define('e')
        second_local_table.define('f')

        @dataclass
        class TestCase:
            table: SymbolTable
            expeced_symbols: List[Symbol]

        tests = [
            TestCase(table=first_local_table,
                     expeced_symbols=[
                        Symbol(name='a', scope=GlobalScope, index=0),
                        Symbol(name='b', scope=GlobalScope, index=1),
                        Symbol(name='c', scope=LocalScope, index=0),
                        Symbol(name='d', scope=LocalScope, index=1),
                     ]),
            TestCase(table=second_local_table,
                     expeced_symbols=[
                        Symbol(name='a', scope=GlobalScope, index=0),
                        Symbol(name='b', scope=GlobalScope, index=1),
                        Symbol(name='e', scope=LocalScope, index=0),
                        Symbol(name='f', scope=LocalScope, index=1),
                     ]),
        ]

        for test in tests:
            for sym in test.expeced_symbols:
                result = test.table.resolve(sym.name)
                self.assertIsNotNone(result, f'name {sym.name} not resolvable')
                self.assertEqual(result, sym, f'expected {sym.name} to resolve to {sym} but got {result}')


if __name__ == '__main__':
    unittest.main()