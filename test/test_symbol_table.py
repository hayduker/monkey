import unittest
from dataclasses import dataclass
from typing import List

from monkey.symbol_table import Symbol, SymbolTable, GlobalScope, LocalScope, BuiltinScope, FreeScope, FunctionScope

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

    def test_define_resolve_builtin(self):
        global_table = SymbolTable()
        first_local_table = SymbolTable(outer=global_table)
        second_local_table = SymbolTable(outer=first_local_table)

        expected = [
            Symbol(name='a', scope=BuiltinScope, index=0),
            Symbol(name='c', scope=BuiltinScope, index=1),
            Symbol(name='e', scope=BuiltinScope, index=2),
            Symbol(name='f', scope=BuiltinScope, index=3),
        ]

        for i, sym in enumerate(expected):
            global_table.define_builtin(i, sym.name)
        
        for table in [global_table, first_local_table, second_local_table]:
            for sym in expected:
                result = table.resolve(sym.name)

                if result is None:
                    self.fail(f'name {sym.name} not resolvable')
                
                if result != sym:
                    self.fail(f'expected {sym.name} to resolve to {sym}, got {result}')

    def test_resolve_free(self):
        global_table = SymbolTable()
        global_table.define('a')
        global_table.define('b')

        first_local_table = SymbolTable(global_table)
        first_local_table.define('c')
        first_local_table.define('d')

        second_local_table = SymbolTable(first_local_table)
        second_local_table.define('e')
        second_local_table.define('f')

        @dataclass
        class Test:
            table: SymbolTable
            expected_symbols: List[Symbol]
            expected_free_symbools: List[Symbol]

        tests = [
            Test(table=first_local_table,
                 expected_symbols=[
                     Symbol(name='a', scope=GlobalScope, index=0),
                     Symbol(name='b', scope=GlobalScope, index=1),
                     Symbol(name='c', scope=LocalScope,  index=0),
                     Symbol(name='d', scope=LocalScope,  index=1),
                 ],
                 expected_free_symbools=[]),
            Test(table=second_local_table,
                 expected_symbols=[
                     Symbol(name='a', scope=GlobalScope, index=0),
                     Symbol(name='b', scope=GlobalScope, index=1),
                     Symbol(name='c', scope=FreeScope,   index=0),
                     Symbol(name='d', scope=FreeScope,   index=1),
                     Symbol(name='e', scope=LocalScope,  index=0),
                     Symbol(name='f', scope=LocalScope,  index=1),
                 ],
                 expected_free_symbools=[
                     Symbol(name='c', scope=LocalScope,  index=0),
                     Symbol(name='d', scope=LocalScope,  index=1),
                 ]),
        ]

        for test in tests:
            for sym in test.expected_symbols:
                result = test.table.resolve(sym.name)

                if result is None:
                    self.fail(f'name {sym.name} not resolvable')

                if result != sym:
                    self.fail(f'expected {sym.name} to resolve to {sym}, got {result}')
                
            if len(test.table.free_symbols) != len(test.expected_free_symbools):
                self.fail(f'wrong number of free symbols. got={len(test.table.free_symbols)}, want={len(test.expected_free_symbools)}')

            for i, sym in enumerate(test.expected_free_symbools):
                result = test.table.free_symbols[i]
                if result != sym:
                    self.fail(f'wrong free symbol. got={result}, want={sym}')
    
    def test_resolve_unresolveable_free(self):
        global_table = SymbolTable()
        global_table.define('a')

        first_local_table = SymbolTable(global_table)
        first_local_table.define('c')

        second_local_table = SymbolTable(first_local_table)
        second_local_table.define('e')
        second_local_table.define('f')

        expected = [
            Symbol(name='a', scope=GlobalScope, index=0),
            Symbol(name='c', scope=FreeScope,   index=0),
            Symbol(name='e', scope=LocalScope,  index=0),
            Symbol(name='f', scope=LocalScope,  index=1),
        ]

        for sym in expected:
            result = second_local_table.resolve(sym.name)

            if result is None:
                self.fail(f'name {sym.name} not resolvable')

            if result != sym:
                self.fail(f'expected {sym.name} to resolve to {sym}, got {result}')
            
            expected_unresolveable = ['b', 'd']
            for name in expected_unresolveable:
                if second_local_table.resolve(name) is not None:
                    self.fail(f'name {name} resolve, but was expected not to')

    def test_define_and_resolve_function_name(self):
        global_table = SymbolTable()
        global_table.define_function_name('a')

        expected = Symbol(name='a', scope=FunctionScope, index=0)

        result = global_table.resolve(expected.name)

        if result is None:
            self.fail(f'function name {expected.name} not resolvable')

        if result != expected:
            self.fail(f'expected {expected.name} to resolve to {expected}, got {result}')
    
    def test_shadowing_function_name(self):
        global_table = SymbolTable()
        global_table.define_function_name('a')
        global_table.define('a')

        expected = Symbol(name='a', scope=GlobalScope, index=0)

        result = global_table.resolve(expected.name)

        if result is None:
            self.fail(f'shadowed name {expected.name} not resolvable')

        if result != expected:
            self.fail(f'expected {expected.name} to resolve to {expected}, got {result}')



if __name__ == '__main__':
    unittest.main()