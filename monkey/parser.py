from typing import Dict, List
from enum import Enum

from monkey.tokens import Token, TokenType
from monkey import myast as ast


class Precedence(Enum):
    LOWEST      = 1
    EQUALS      = 2 # ==
    LESSGREATER = 3 # > or <
    SUM         = 4 # +
    PRODUCT     = 5 # *
    PREFIX      = 6 # -X or !X
    CALL        = 7 # myFunction(X)
    INDEX       = 8 # myArray[X]

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

class PrefixParseFn:
    def __call__(self) -> ast.Expression:
        pass


class InfixParseFn:
    def __call__(self, lhs: ast.Expression) -> ast.Expression:
        pass


class Parser:
    def __init__(self, lexer):
        self.depth = 0
        self.verbose = False
        self.tokens = []

        self.lexer: Lexer = lexer
        self.curr_token: Token = None
        self.peek_token: Token = None
        self.errors: List[str] = []

        self.operator_precedences = {
            TokenType.EQ:       Precedence.EQUALS,
            TokenType.NOT_EQ:   Precedence.EQUALS,
            TokenType.LT:       Precedence.LESSGREATER,
            TokenType.GT:       Precedence.LESSGREATER,
            TokenType.PLUS:     Precedence.SUM,
            TokenType.MINUS:    Precedence.SUM,
            TokenType.SLASH:    Precedence.PRODUCT,
            TokenType.ASTERISK: Precedence.PRODUCT,
            TokenType.LPAREN:   Precedence.CALL,
            TokenType.LBRACKET: Precedence.INDEX,
        }

        self.prefix_parse_fns: Dict[TokenType, PrefixParseFn] = {}
        self.register_prefix(TokenType.IDENT,    self.parse_identifier)
        self.register_prefix(TokenType.INT,      self.parse_integer_literal)
        self.register_prefix(TokenType.STRING,   self.parse_string_literal)
        self.register_prefix(TokenType.TRUE,     self.parse_boolean)
        self.register_prefix(TokenType.FALSE,    self.parse_boolean)
        self.register_prefix(TokenType.BANG,     self.parse_prefix_expression)
        self.register_prefix(TokenType.MINUS,    self.parse_prefix_expression)
        self.register_prefix(TokenType.LPAREN,   self.parse_grouped_expression)
        self.register_prefix(TokenType.LBRACKET, self.parse_array_literal)
        self.register_prefix(TokenType.LBRACE,   self.parse_hash_literal)
        self.register_prefix(TokenType.IF,       self.parse_if_expression)
        self.register_prefix(TokenType.FUNCTION, self.parse_function_literal)

        self.infix_parse_fns: Dict[TokenType, InfixParseFn]  = {}
        self.register_infix(TokenType.PLUS,      self.parse_infix_expression)
        self.register_infix(TokenType.MINUS,     self.parse_infix_expression)
        self.register_infix(TokenType.SLASH,     self.parse_infix_expression)
        self.register_infix(TokenType.ASTERISK,  self.parse_infix_expression)
        self.register_infix(TokenType.EQ,        self.parse_infix_expression)
        self.register_infix(TokenType.NOT_EQ,    self.parse_infix_expression)
        self.register_infix(TokenType.LT,        self.parse_infix_expression)
        self.register_infix(TokenType.GT,        self.parse_infix_expression)
        self.register_infix(TokenType.LPAREN,    self.parse_call_expression)
        self.register_infix(TokenType.LBRACKET,  self.parse_index_expression)

        self.next_token()
        self.next_token()

    def spaces(self):
        return 2*self.depth*' '
    
    def parse_program(self) -> ast.Program:
        self.verbose and print()
        program = ast.Program()

        while not self.curr_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            
            self.next_token()
        
        return program
    
    ##################################
    # Methods for parsing statements #
    ##################################

    def parse_statement(self) -> ast.Statement:        
        match self.curr_token.type:
            case TokenType.LET:
                return self.parse_let_statement()
            case TokenType.RETURN:
                return self.parse_return_statement()
            case _:
                return self.parse_expression_statement()

    def parse_let_statement(self) -> ast.LetStatement:
        stmt = ast.LetStatement(self.curr_token)
        
        if not self.expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = ast.Identifier(token=self.curr_token, value=self.curr_token.literal)

        if not self.expect_peek(TokenType.ASSIGN):
            return None

        self.next_token()
        stmt.value = self.parse_expression(Precedence.LOWEST)

        if type(stmt.value) is ast.FunctionLiteral:
            stmt.value.name = stmt.name.value
        
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        return stmt
    
    def parse_return_statement(self) -> ast.ReturnStatement:
        stmt = ast.ReturnStatement(self.curr_token)

        self.next_token()
        stmt.return_value = self.parse_expression(Precedence.LOWEST)

        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        return stmt

    def parse_expression_statement(self) -> ast.ExpressionStatement:
        self.verbose and print(f'{self.spaces()} parse_expression_statement: {self.curr_token}')

        stmt = ast.ExpressionStatement(self.curr_token)
        stmt.expression = self.parse_expression(Precedence.LOWEST)

        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        
        return stmt

    ###################################
    # Methods for parsing expressions #
    ###################################

    def parse_expression(self, precedence: Precedence) -> ast.Expression:
        self.depth += 1

        self.verbose and print(f'{self.spaces()} parse_expression: curr_token={self.curr_token}, precedence={precedence}')

        prefix = self.prefix_parse_fns.get(self.curr_token.type, None)
        if prefix is None:
            self.verbose and print(f'{self.spaces()} parse_expression: no prefix parse fn')
            self.no_prefix_parse_fn_error(self.curr_token.type)
            return None
        
        self.verbose and print(f'{self.spaces()} parse_expression: calling prefix {prefix.__name__}')
        left_exp = prefix()
        self.verbose and print(f'{self.spaces()} parse_expression: got left exp {left_exp}, peek token is {self.peek_token}')

        while not self.peek_token_is(TokenType.SEMICOLON) and precedence < self.peek_precedence():
            infix = self.infix_parse_fns[self.peek_token.type]
            if infix is None:
                self.verbose and print(f'{self.spaces()} parse_expression: no infix fn, left_exp = {left_exp}')
                return left_exp
            self.verbose and print(f'{self.spaces()} parse_expression: got infix fn = {infix.__name__}, nexting token')
            
            self.next_token()
            left_exp = infix(left_exp)
            self.verbose and print(f'{self.spaces()} parse_expression: reset left exp to {left_exp}')

        self.verbose and print(f'{self.spaces()} parse_expression: returning left_exp = {left_exp}')
        self.depth -= 1
        return left_exp

    def parse_identifier(self) -> ast.Identifier:
        return ast.Identifier(token=self.curr_token, value=self.curr_token.literal)

    def parse_integer_literal(self) -> ast.IntegerLiteral:
        literal = ast.IntegerLiteral(self.curr_token)

        try:
            literal.value = int(self.curr_token.literal)
        except ValueError:
            msg = f'Could not parse "{self.curr_token.literal}" as integer.'
            self.errors.append(msg)
            return None
        
        return literal

    def parse_string_literal(self) -> ast.StringLiteral:
        return ast.StringLiteral(self.curr_token, self.curr_token.literal)

    def parse_boolean(self) -> ast.Boolean:
        return ast.Boolean(token=self.curr_token,
                           value=self.curr_token_is(TokenType.TRUE))

    def parse_prefix_expression(self) -> ast.PrefixExpression:
        expression = ast.PrefixExpression(token=self.curr_token,
                                          operator=self.curr_token.literal)
        
        # Prefix expression must consume more than one token, so we advance
        # to the next token and call parse_expression again to collect the 
        # right-hand side of the prefix expression
        self.next_token()
        expression.right = self.parse_expression(Precedence.PREFIX)
        return expression

    def parse_infix_expression(self, left: ast.Expression) -> ast.InfixExpression:
        self.depth += 1

        expression = ast.InfixExpression(token=self.curr_token,
                                         left=left,
                                         operator=self.curr_token.literal)
    
        self.verbose and print(f'{self.spaces()} parse_infix_expression: created expression(curr_token/operator={self.curr_token}, left={left})')
        precedence = self.curr_precedence()
        self.verbose and print(f'{self.spaces()} parse_infix_expression: nexting token, calling parse_expression with precedence {precedence}')
        self.next_token()
        expression.right = self.parse_expression(precedence)
        self.verbose and print(f'{self.spaces()} parse_infix_expression: got right side = {expression.right}')

        self.depth -= 1
        return expression

    def parse_grouped_expression(self) -> ast.Expression:
        self.next_token()

        expression = self.parse_expression(Precedence.LOWEST)
        if not self.expect_peek(TokenType.RPAREN):
            return None

        return expression

    def parse_block_statement(self):
        block = ast.BlockStatement(self.curr_token)
        self.next_token()

        while not self.curr_token_is(TokenType.RBRACE) and not self.curr_token_is(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                block.statements.append(stmt)
            self.next_token()
        
        return block

    def parse_if_expression(self) -> ast.IfExpression:
        expression = ast.IfExpression(self.curr_token)

        if not self.expect_peek(TokenType.LPAREN):
            return None
        
        self.next_token()
        expression.condition = self.parse_expression(Precedence.LOWEST)

        if not self.expect_peek(TokenType.RPAREN):
            return None
        
        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        expression.consequence = self.parse_block_statement()

        if self.peek_token_is(TokenType.ELSE):
            self.next_token() # else
            if not self.expect_peek(TokenType.LBRACE):
                return None

            expression.alternative = self.parse_block_statement()

        return expression
    
    def parse_function_parameters(self) -> list[ast.Identifier]:
        parameters = []

        self.next_token()
        if not self.curr_token_is(TokenType.RPAREN):
            while True:
                parameters.append(self.parse_identifier())

                if self.peek_token_is(TokenType.RPAREN):
                    self.next_token()
                    break

                if not self.expect_peek(TokenType.COMMA):
                    return None
                
                self.next_token()

        return parameters

    def parse_function_literal(self) -> ast.FunctionLiteral:
        function = ast.FunctionLiteral(self.curr_token)

        if not self.expect_peek(TokenType.LPAREN):
            return None

        function.parameters = self.parse_function_parameters()

        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        function.body = self.parse_block_statement()

        return function

    def parse_call_expression(self, function: ast.Expression) -> ast.CallExpression:
        call = ast.CallExpression(token=self.curr_token,
                                  function=function)
        call.arguments = self.parse_expresion_list(TokenType.RPAREN)
        return call

    def parse_array_literal(self) -> ast.ArrayLiteral:
        array = ast.ArrayLiteral(self.curr_token)
        array.elements = self.parse_expresion_list(TokenType.RBRACKET)
        return array
    
    def parse_hash_literal(self) -> ast.HashLiteral:
        hush = ast.HashLiteral(self.curr_token)

        while not self.peek_token_is(TokenType.RBRACE):
            self.next_token()
            key = self.parse_expression(Precedence.LOWEST)

            if not self.expect_peek(TokenType.COLON):
                return None
            
            self.next_token()
            value = self.parse_expression(Precedence.LOWEST)

            hush.pairs[key] = value

            if not self.peek_token_is(TokenType.RBRACE) and not self.expect_peek(TokenType.COMMA):
                return None
        
        if not self.expect_peek(TokenType.RBRACE):
            return None

        return hush

    def parse_index_expression(self, left: ast.Expression) -> ast.IndexExpression:
        exp = ast.IndexExpression(token=self.curr_token,
                                               left=left)

        self.next_token()
        exp.index = self.parse_expression(Precedence.LOWEST)
        if not self.expect_peek(TokenType.RBRACKET):
            return None

        return exp

    ##########################
    # Various helper methods #
    ##########################

    def parse_expresion_list(self, end: TokenType) -> list[ast.Expression]:
        expressions = []
        
        self.next_token()
        if not self.curr_token_is(end):
            while True:
                expressions.append(self.parse_expression(Precedence.LOWEST))

                if self.peek_token_is(end):
                    self.next_token()
                    break

                if not self.expect_peek(TokenType.COMMA):
                    return None
                
                self.next_token()

        return expressions

    def expect_peek(self, t: TokenType) -> bool:
        if self.peek_token_is(t):
            self.next_token()
            return True

        self.peek_error(t)
        return False

    def next_token(self):
        self.curr_token = self.peek_token
        self.peek_token = self.lexer.next_token()
        if len(self.tokens) > 0 and self.tokens[-1].type == TokenType.EOF:
            pass
        else:
            self.tokens.append(self.peek_token)

    def curr_token_is(self, t: TokenType) -> bool:
        return self.curr_token.type == t

    def peek_token_is(self, t: TokenType) -> bool:
        return self.peek_token.type == t

    def curr_precedence(self) -> int:
        return self.operator_precedences.get(self.curr_token.type, Precedence.LOWEST)

    def peek_precedence(self) -> int:
        return self.operator_precedences.get(self.peek_token.type, Precedence.LOWEST)

    def peek_error(self, t: TokenType):
        msg = f'Expected next token to be {t}, got {self.peek_token.type} instead.'
        self.errors.append(msg)

    def no_prefix_parse_fn_error(self, t: TokenType) -> ast.Expression:
        msg = f'No prefix parse function for {t} found.'
        self.errors.append(msg)

    def get_errors(self):
        return self.errors
    
    def register_prefix(self, token_type: TokenType, fn: PrefixParseFn):
        self.prefix_parse_fns[token_type] = fn

    def register_infix(self, token_type: TokenType, fn: InfixParseFn):
        self.infix_parse_fns[token_type] = fn