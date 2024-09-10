import unittest

from monkey.symbol_table import Symbol, SymbolTable, GlobalScope

class TestSymbolTable(unittest.TestCase):
    def test_define(self):
        expected = {
            'a': Symbol(name='a', scope=GlobalScope, index=0),
            'b': Symbol(name='b', scope=GlobalScope, index=1),
        }

        global_table = SymbolTable()

        a = global_table.define('a')
        self.assertEqual(a, expected['a'])

        b = global_table.define('b')
        self.assertEqual(b, expected['b'])

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
            if result is None:
                self.fail(f'symbol {sym.name} not resolvable')
            if result != sym:
                self.fail(f'expected {sym.name} to resolve to {sym} but got {result}')


if __name__ == '__main__':
    unittest.main()