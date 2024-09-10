from enum import Enum
from dataclasses import dataclass

# Token types in Monkey
class TokenType(Enum):
    ILLEGAL = 'ILLEGAL'
    EOF     = 'EOF'

    # Identifiers + literals
    IDENT = 'IDENT' # add, foobar, x, y, ...
    INT   = 'INT'   # 1343456

    # Operators
    ASSIGN   = 'ASSIGN'
    PLUS     = 'PLUS'
    MINUS    = 'MINUS'
    BANG     = 'BANG'
    ASTERISK = 'ASTERISK'
    SLASH    = 'SLASH'

    LT = 'LT'
    GT = 'GT'

    EQ     = 'EQ'
    NOT_EQ = 'NOT_EQ'

    # Delimiters
    COMMA     = 'COMMA'
    COLON     = 'COLON'
    SEMICOLON = 'SEMICOLON'
    LPAREN    = 'LPAREN'
    RPAREN    = 'RPAREN'
    LBRACKET  = 'LBRACKET'
    RBRACKET  = 'RBRACKET'
    LBRACE    = 'LBRACE'
    RBRACE    = 'RBRACE'

    # Keywords
    FUNCTION = 'FUNCTION'
    LET      = 'LET'
    TRUE     = 'TRUE'
    FALSE    = 'FALSE'
    IF       = 'IF'
    ELSE     = 'ELSE'
    RETURN   = 'RETURN'

    # Strings
    STRING   = 'STRING'

keywords = {
    'fn':     TokenType.FUNCTION,
    'let':    TokenType.LET,
    'true':   TokenType.TRUE,
    'false':  TokenType.FALSE,
    'if':     TokenType.IF,
    'else':   TokenType.ELSE,
    'return': TokenType.RETURN,
}

def lookup_identifier(identifier_literal: str) -> TokenType:
    '''
    Checks if the literal is a specific keyword, or just an identifier,
    returning the appropriate TokenType
    '''
    return keywords.get(identifier_literal, TokenType.IDENT)


class Token:
    def __init__(self, tok_type: TokenType, tok_literal: str):
        self.type = tok_type
        self.literal = tok_literal

    def __repr__(self):
        string = self.type.value
        if string in ['INT', 'IDENT']:
            string += f'({self.literal})'
        return string


__all__ = ['TokenType', 'Token', 'lookup_identifier']