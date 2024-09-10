import monkey.myast as ast
import monkey.object as qobj
from monkey.object import *
from monkey.builtins import builtins
from monkey.tokens import TokenType, Token

from typing import Hashable

class Evaluator:

    def evaluate(self, node, env: Environment):
        match type(node):
            # Statements
            case ast.Program:
                return self.evaluate_program(node.statements, env)
            case ast.BlockStatement:
                return self.evaluate_block_statement(node, env)
            case ast.LetStatement:
                value = self.evaluate(node.value, env)
                if is_error(value):
                    return value
                env.set(node.name.value, value)
            case ast.ReturnStatement:
                value = self.evaluate(node.return_value, env)
                if is_error(value):
                    return value
                return ReturnValue(value=value)
            case ast.ExpressionStatement:
                return self.evaluate(node.expression, env)
            
            # Expressions
            case ast.IntegerLiteral:
                return IntegerObject(value=node.value)
            case ast.StringLiteral:
                return StringObject(value=node.value)
            case ast.Boolean:
                return self.native_bool_to_object(node.value)
            case ast.PrefixExpression:
                right = self.evaluate(node.right, env)
                if is_error(right):
                    return right 
                return self.evaluate_prefix_expression(node.operator, right)
            case ast.InfixExpression:
                left = self.evaluate(node.left, env)
                if is_error(left):
                    return left
                right = self.evaluate(node.right, env)
                if is_error(right):
                    return right
                return self.evaluate_infix_expression(left, node.operator, right)
            case ast.IfExpression:
                return self.evaluate_if_expression(node, env)
            case ast.Identifier:
                return self.evaluate_identifier(node, env)
            case ast.FunctionLiteral:
                params = node.parameters
                body   = node.body
                return FunctionObject(params, body, env)
            case ast.CallExpression:
                if node.function.token_literal() == 'quote':
                    return self.quote(node.arguments[0], env)
                
                fn = self.evaluate(node.function, env)
                if is_error(fn):
                    return fn

                args = self.evaluate_expressions(node.arguments, env)
                if len(args) == 1 and is_error(args[0]):
                    return args[0]

                return self.apply_function(fn, args)
            case ast.ArrayLiteral:
                elements = self.evaluate_expressions(node.elements, env)
                if len(elements) == 1 and is_error(elements[0]):
                    return elements[0]
                
                return ArrayObject(elements=elements)
            case ast.IndexExpression:
                left = self.evaluate(node.left, env)
                if is_error(left):
                    return left
                
                index = self.evaluate(node.index, env)
                if is_error(index):
                    return index
                
                return self.evaluate_index_expression(left, index)
            case ast.HashLiteral:
                return self.evaluate_hash_literal(node, env)
                
    def evaluate_program(self, statements: list[ast.Statement], env: Environment) -> Object:
        for stmt in statements:
            result = self.evaluate(stmt, env)
            if type(result) is ReturnValue:
                return result.value
            elif type(result) is ErrorObject:
                return result
        
        return result

    def evaluate_block_statement(self, block: ast.BlockStatement, env: Environment) -> Object:
        for stmt in block.statements:
            result = self.evaluate(stmt, env)

            if result is not None:
                if result.objtype() in [ObjectType.RETURN_VALUE_OBJ, ObjectType.ERROR_OBJ]:
                    return result

        return result

    def evaluate_expressions(self, expressions: list[ast.Expression], env: Environment) -> list[Object]:
        results = []
        for expr in expressions:
            evaluated = self.evaluate(expr, env)
            if is_error(evaluated):
                return [evaluated]

            results.append(evaluated)

        return results

    def evaluate_prefix_expression(self, operator: str, right: Object) -> Object:
        match operator:
            case '!':
                return self.evaluate_bang_operator_expression(right)
            case '-':
                return self.evaluate_minus_prefix_operator_expression(right)
            case _:
                return new_error(message=f'unknown operator: {operator}{right.objtype().value}')

    def evaluate_bang_operator_expression(self, right: Object) -> BooleanObject:
        match right:
            case qobj.TRUE:
                return qobj.FALSE
            case qobj.FALSE:
                return qobj.TRUE
            case qobj.NULL:
                return qobj.TRUE
            case _:
                return qobj.FALSE

    def evaluate_minus_prefix_operator_expression(self, right: Object) -> IntegerObject:
        if type(right) is IntegerObject:
            return IntegerObject(-1 * right.value)
        else:
            return new_error(message=f'unknown operator: -{right.objtype().value}')

    def evaluate_infix_expression(self, left: Object, operator: str, right: Object) -> Object:
        if left.objtype() == ObjectType.INTEGER_OBJ and right.objtype() == ObjectType.INTEGER_OBJ:
            return self.evaluate_integer_infix_expression(left, operator, right)
        elif left.objtype() == ObjectType.STRING_OBJ and right.objtype() == ObjectType.STRING_OBJ:
            return self.evaluate_string_infix_expression(left, operator, right)
        elif operator == '==':
            return self.native_bool_to_object(left == right)
        elif operator == '!=':
            return self.native_bool_to_object(left != right)
        elif left.objtype() != right.objtype():
            return new_error(message=f'type mismatch: {left.objtype().value} {operator} {right.objtype().value}')
        else:
            return new_error(message=f'unknown operator: {left.objtype().value} {operator} {right.objtype().value}')

    def evaluate_integer_infix_expression(self, left: Object, operator: str, right: Object) -> Object:
        match operator:
            case '+':
                return IntegerObject(left.value + right.value)
            case '-':
                return IntegerObject(left.value - right.value)
            case '*':
                return IntegerObject(left.value * right.value)
            case '/':
                return IntegerObject(int(left.value / right.value))
            case '>':
                return self.native_bool_to_object(left.value > right.value)
            case '<':
                return self.native_bool_to_object(left.value < right.value)
            case '==':
                return self.native_bool_to_object(left.value == right.value)
            case '!=':
                return self.native_bool_to_object(left.value != right.value)
            case _:
                return new_error(message=f'unknown operator: {left.objtype().value} {operator} {right.objtype().value}')

    def evaluate_string_infix_expression(self, left: Object, operator: str, right: Object) -> Object:
        if operator != '+':
            return new_error(message=f'unknown operator: {left.objtype().value} {operator} {right.objtype().value}')
        
        return StringObject(left.value + right.value)

    def evaluate_if_expression(self, expression: ast.IfExpression, env: Environment) -> Object:
        condition = self.evaluate(expression.condition, env)
        if self.is_truthy(condition):
            return self.evaluate(expression.consequence, env)
        elif expression.alternative is not None:
            return self.evaluate(expression.alternative, env)
        else:
            return qobj.NULL

    def evaluate_identifier(self, node: ast.Identifier, env: Environment) -> Object:
        value = env.get(node.value)
        if value is not None:
            return value

        builtin = builtins.get(node.value, None)
        if builtin is not None:
            return builtin

        return new_error(f'identifier not found: {node.value}')

    #######################
    # Function evaluation #
    #######################

    def apply_function(self, function: Object, args: list[Object]) -> Object:
        if type(function) == FunctionObject:
            # TODO: After evaluation, we could set function.env to be the new
            # version of extended_env but without the args, that way function
            # state isn't just read-only
            extended_env = self.extend_function_env(function, args)
            evaluated = self.evaluate(function.body, extended_env)
            return self.unwrap_return_value(evaluated)

        elif type(function) == BuiltinObject:
            return function.fn(args)
        
        return new_error(f'not a function: {function.objtype()}')

    def extend_function_env(self, fn: FunctionObject, args: list[Object]) -> Environment:
        env = Environment(outer=fn.env)
        for i, param in enumerate(fn.parameters):
            env.set(param.value, args[i])
        return env

    def unwrap_return_value(self, obj: Object) -> Object:
        return obj.value if type(obj) == ReturnValue else obj

    #####################
    # Arrays and hashes #
    #####################

    def evaluate_index_expression(self, left: Object, index: Object) -> Object:
        if left.objtype() == ObjectType.ARRAY_OBJ and index.objtype() == ObjectType.INTEGER_OBJ:
            return self.evaluate_array_index_expression(left, index)
        elif left.objtype() == ObjectType.HASH_OBJ:
            return self.evaluate_hash_index_expression(left, index)
        else:
            return self.new_error(f'index operator not supported: {left.objtype()}')
    
    def evaluate_array_index_expression(self, array: ArrayObject, index: IntegerObject) -> Object:
        idx = index.value
        if idx < 0 or idx > len(array.elements)-1:
            return qobj.NULL
        
        return array.elements[idx]

    def evaluate_hash_literal(self, node: ast.HashLiteral, env: Environment):
        pairs = {}

        for key_node, value_node in node.pairs.items():
            key = self.evaluate(key_node, env)
            if self.is_error(key):
                return key

            value = self.evaluate(value_node, env)
            if self.is_error(value):
                return value

            pairs[key] = value

        return HashObject(pairs=pairs)

    def evaluate_hash_index_expression(self, hush: HashObject, key: Object) -> Object:
        if not isinstance(key, Hashable):
            return self.new_error(f'unusable as hash key: {key.objtype()}')
        
        value = hush.pairs.get(key, None)
        if value is None:
            return NULL
        
        return value

    ####################
    # Macro evaluation #
    ####################

    def quote(self, node: ast.Node, env: Environment) -> Object:
        node = self.eval_unquote_calls(node, env)
        return QuoteObject(node=node)
    
    def eval_unquote_calls(self, quoted: ast.Node, env: Environment) -> ast.Node:
        def unquoter(node):
            if not self.is_unquote_call(node):
                return node
        
            if type(node) is not ast.CallExpression:
                return node
            
            if len(node.arguments) != 1:
                return node
            
            unquoted = self.evaluate(node.arguments[0], env)
            return self.convert_object_to_ast_node(unquoted)
        
        return ast.modify(quoted, unquoter)
    
    def is_unquote_call(self, node: ast.Node) -> bool:
        if type(node) is not ast.CallExpression:
            return False
        
        return node.function.token_literal() == 'unquote'

    def convert_object_to_ast_node(self, obj: Object) -> ast.Node:
        if type(obj) is IntegerObject:
            t = Token(tok_type=TokenType.INT,
                      tok_literal=str(obj.value))
            return ast.IntegerLiteral(token=t, value=obj.value)
        elif type(obj) is BooleanObject:
            if obj.value:
                tok_type=TokenType.TRUE
                tok_literal='true'
            else:
                tok_type=TokenType.FALSE
                tok_literal='false'
            return ast.Boolean(token=Token(tok_type, tok_literal), value=tok_literal)
        elif type(obj) is QuoteObject:
            return obj.node
        else:
            return None

    ##################
    # Helper methods #
    ##################

    def is_truthy(self, obj: Object) -> bool:
        return False if obj == qobj.NULL or obj == qobj.FALSE else True

    def native_bool_to_object(self, value):
        return qobj.TRUE if value else qobj.FALSE

    def new_error(self, message: str) -> ErrorObject:
        return ErrorObject(message)

    def is_error(self, obj: Object) -> bool:
        return obj is not None and obj.objtype() == ObjectType.ERROR_OBJ