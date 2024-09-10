import unittest
from dataclasses import dataclass

from monkey.tokens import Token, TokenType
from monkey import myast as ast

class AstTestCase(unittest.TestCase):

    def test_repr(self):
        program = ast.Program()
        program.statements = [
            ast.LetStatement(
                token = Token(TokenType.LET, 'let'),
                name = ast.Identifier(
                    token = Token(TokenType.IDENT, 'myVar'),
                    value = 'myVar'
                ),
                value = ast.Identifier(
                    token = Token(TokenType.IDENT, 'anotherVar'),
                    value = 'anotherVar'
                )
            )
        ]

        self.assertEqual(str(program), 'let myVar = anotherVar;')

    def test_modify(self):
        one = lambda: ast.IntegerLiteral(token=None, value=1)
        two = lambda: ast.IntegerLiteral(token=None, value=2)

        def turn_one_into_two(node: ast.Node) -> ast.Node:
            if type(node) is not ast.IntegerLiteral:
                return node

            if node.value != 1:
                return node
            
            node.value = 2
            return node
        
        @dataclass
        class Test:
            input_node: ast.Node
            expected: ast.Node

        tests = [
            Test(one(), two()),

            Test(ast.Program(
                    statements=[ast.ExpressionStatement(token=None, expression=one())]
                 ),
                 ast.Program(
                    statements=[ast.ExpressionStatement(token=None, expression=two())]
                 )),

            Test(ast.InfixExpression(token=None, left=one(), operator='+', right=two()),
                 ast.InfixExpression(token=None, left=two(), operator='+', right=two())),

            Test(ast.InfixExpression(token=None, left=two(), operator='+', right=one()),
                 ast.InfixExpression(token=None, left=two(), operator='+', right=two())),

            Test(ast.PrefixExpression(token=None, operator='-', right=one()),
                 ast.PrefixExpression(token=None, operator='-', right=two())),

            Test(ast.IndexExpression(token=None, left=one(), index=one()),
                 ast.IndexExpression(token=None, left=two(), index=two())),
            
            Test(ast.IfExpression(token=None,
                                  condition=one(), 
                                  consequence=ast.BlockStatement(
                                    token=None,
                                    statements=[ast.ExpressionStatement(token=None, expression=one())]
                                  ),
                                  alternative=ast.BlockStatement(
                                    token=None,
                                    statements=[ast.ExpressionStatement(token=None, expression=one())]
                                  )),
                ast.IfExpression(token=None,
                                  condition=two(), 
                                  consequence=ast.BlockStatement(
                                    token=None,
                                    statements=[ast.ExpressionStatement(token=None, expression=two())]
                                  ),
                                  alternative=ast.BlockStatement(
                                    token=None,
                                    statements=[ast.ExpressionStatement(token=None, expression=two())]
                                  ))),

            Test(ast.ReturnStatement(token=None, return_value=one()),
                 ast.ReturnStatement(token=None, return_value=two())),
            
            Test(ast.LetStatement(token=None, value=one()),
                 ast.LetStatement(token=None, value=two())),
            
            Test(ast.FunctionLiteral(
                token=None,
                parameters=[],
                body=ast.BlockStatement(
                    token=None,
                    statements=[
                        ast.ExpressionStatement(token=None, expression=one())
                    ]
                )),
                ast.FunctionLiteral(
                    token=None,
                    parameters=[],
                    body=ast.BlockStatement(
                        token=None,
                        statements=[
                            ast.ExpressionStatement(token=None, expression=two())
                        ]
                    ))),
        
            Test(ast.ArrayLiteral(token=None, elements=[one(), one()]),
                 ast.ArrayLiteral(token=None, elements=[two(), two()])),
                
            Test(ast.HashLiteral(
                    token=None,
                    pairs={
                        one(): one(),
                        one(): one()
                    }
                ),
                ast.HashLiteral(
                    token=None,
                    pairs={
                        two(): two(),
                        two(): two()
                    }
                ))
        ]

        for test in tests:
            modified = ast.modify(test.input_node, turn_one_into_two)
            self.assertEqual(modified, test.expected)

        # # HashLiterals are handled a little differntly
        # hash_literal = ast.HashLiteral(
        #     token=None,
        #     pairs={
        #         one(): one(),
        #         one(): one()
        #     }
        # )

        # modify(hash_literal, turn_one_into_two)

        # for k, v in hash_literal.pairs.items():
        #     self.assertEqual

if __name__ == '__main__':
    unittest.main(verbosity=2)