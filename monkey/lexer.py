from monkey.tokens import Token, TokenType, lookup_identifier

class Lexer:
    def __init__(self, input_string):
        self.input = input_string
        self.position = -1 # current position in input (points to current char)
        self.read_position = 0 # current reading position in input (after current char)
        self.ch = None # current char under examination

        self.read_char() # Loads the first char and associated positions

    def next_token(self) -> Token:
        tok = None

        self.skip_whitespace()

        match self.ch:
            case '=':
                if self.peek_char() == '=':
                    ch = self.ch
                    self.read_char()
                    tok = Token(TokenType.EQ, ch + self.ch)
                else:
                    tok = Token(TokenType.ASSIGN, self.ch)
            case '+':
                tok = Token(TokenType.PLUS, self.ch)
            case '-':
                tok = Token(TokenType.MINUS, self.ch)
            case '!':
                if self.peek_char() == '=':
                    ch = self.ch
                    self.read_char()
                    tok = Token(TokenType.NOT_EQ, ch + self.ch)
                else:
                    tok = Token(TokenType.BANG, self.ch)
            case '/':
                tok = Token(TokenType.SLASH, self.ch)
            case '*':
                tok = Token(TokenType.ASTERISK, self.ch)
            case '<':
                tok = Token(TokenType.LT, self.ch)
            case '>':
                tok = Token(TokenType.GT, self.ch)
            case ';':
                tok = Token(TokenType.SEMICOLON, self.ch)
            case ',':
                tok = Token(TokenType.COMMA, self.ch)
            case ':':
                tok = Token(TokenType.COLON, self.ch)
            case '(':
                tok = Token(TokenType.LPAREN, self.ch)
            case ')':
                tok = Token(TokenType.RPAREN, self.ch)
            case '[':
                tok = Token(TokenType.LBRACKET, self.ch)
            case ']':
                tok = Token(TokenType.RBRACKET, self.ch)
            case '{':
                tok = Token(TokenType.LBRACE, self.ch)
            case '}':
                tok = Token(TokenType.RBRACE, self.ch)
            case None:
                tok = Token(TokenType.EOF, '')
            case '"':
                token_type = TokenType.STRING
                literal = self.read_string()
                return Token(token_type, literal)
            case _:
                if self.is_letter(self.ch):
                    literal = self.read_identifier()
                    token_type = lookup_identifier(literal)
                    return Token(token_type, literal)
                elif self.is_digit(self.ch):
                    token_type = TokenType.INT
                    literal = self.read_number()
                    return Token(token_type, literal)
                else:
                    tok = Token(ILLEGAL, self.ch)

        self.read_char()
        return tok

    def is_letter(self, ch):
        return ch is not None and (ch.isalpha() or ch == '_')

    def read_identifier(self):
        position = self.position
        while self.is_letter(self.ch):
            self.read_char()
        return self.input[position:self.position]

    def is_digit(self, ch):
        return ch is not None and ch.isdigit()

    def read_number(self):
        position = self.position
        while self.is_digit(self.ch):
            self.read_char()
        return self.input[position:self.position]

    def read_string(self):
        self.read_char() # Consume the leading " since we don't need it
        position = self.position
        while self.ch != '"':
            self.read_char()
        literal = self.input[position:self.position]
        self.read_char() # Consume the trailing " since we don't need it
        return literal

    def peek_char(self):
        return self.input[self.read_position] if self.read_position < len(self.input) else None

    def read_char(self):
        self.ch = self.input[self.read_position] if self.read_position < len(self.input) else None
        self.position = self.read_position
        self.read_position += 1

    def skip_whitespace(self):
        while self.ch is not None and self.ch.isspace():
            self.read_char()