"""
scanner.py
"""

import sys

# Token type constants
LOAD, LOADI, STORE, ADD, SUB, MULT = 0, 1, 2, 3, 4, 5
LSHIFT, RSHIFT, OUTPUT, NOP = 6, 7, 8, 9
REGISTER, CONSTANT, COMMA, ARROW = 10, 11, 12, 13
ENDLINE, EOF, ERROR = 14, 15, 16

class TokenType:
    LOAD, LOADI, STORE = LOAD, LOADI, STORE
    ADD, SUB, MULT = ADD, SUB, MULT
    LSHIFT, RSHIFT = LSHIFT, RSHIFT
    OUTPUT, NOP = OUTPUT, NOP
    REGISTER, CONSTANT = REGISTER, CONSTANT
    COMMA, ARROW = COMMA, ARROW
    ENDLINE, EOF, ERROR = ENDLINE, EOF, ERROR

class Token:
    __slots__ = ['type', 'lexeme', 'line', 'value']
    
    def __init__(self, token_type, lexeme, line, value=None):
        self.type = token_type
        self.lexeme = lexeme
        self.line = line
        self.value = value

class Scanner:
    __slots__ = ['input', 'length', 'pos', 'line', '_opcodes', '_type_strings']
    
    def __init__(self, filename):
        try:
            # Read file in chunks to avoid memory spikes
            with open(filename, 'r', buffering=8192) as f:
                self.input = f.read()
        except IOError:
            print(f"ERROR: Cannot read file '{filename}'", file=sys.stderr)
            sys.exit(1)
        
        self.length = len(self.input)
        self.pos = 0
        self.line = 1
        
        # Store these as instance variables to avoid class lookup
        self._opcodes = {
            'load': LOAD, 'loadI': LOADI, 'store': STORE,
            'add': ADD, 'sub': SUB, 'mult': MULT,
            'lshift': LSHIFT, 'rshift': RSHIFT,
            'output': OUTPUT, 'nop': NOP
        }
        
        self._type_strings = [
            "MEMOP", "LOADI", "MEMOP", "ARITHOP", "ARITHOP",
            "ARITHOP", "ARITHOP", "ARITHOP", "OUTPUT", "NOP",
            "REGISTER", "CONSTANT", "COMMA", "INTO", "ENDLINE",
            "EOF", "ERROR"
        ]
    
    def next_token(self):
        """Scan next token with minimal overhead"""
        pos = self.pos
        input_str = self.input
        length = self.length
        
        # Skip whitespace and comments
        while pos < length:
            ch = input_str[pos]
            if ch == ' ' or ch == '\t':
                pos += 1
                continue
            if ch == '/':
                if pos + 1 < length and input_str[pos + 1] == '/':
                    # Skip comment
                    pos += 2
                    while pos < length and input_str[pos] not in '\n\r':
                        pos += 1
                    continue
            break
        
        # Update position
        self.pos = pos
        
        # Check EOF
        if pos >= length:
            return Token(EOF, '', self.line)
        
        ch = input_str[pos]
        
        # Handle newlines
        if ch == '\n' or ch == '\r':
            pos += 1
            # Handle \r\n or \n\r
            if pos < length:
                next_ch = input_str[pos]
                if (ch == '\n' and next_ch == '\r') or (ch == '\r' and next_ch == '\n'):
                    pos += 1
            self.pos = pos
            line = self.line
            self.line += 1
            return Token(ENDLINE, '\\n', line)
        
        # Simple tokens
        if ch == ',':
            self.pos = pos + 1
            return Token(COMMA, ',', self.line)
        
        if ch == '=':
            if pos + 1 < length and input_str[pos + 1] == '>':
                self.pos = pos + 2
                return Token(ARROW, '=>', self.line)
        
        # Numbers
        if '0' <= ch <= '9':
            start = pos
            while pos < length and '0' <= input_str[pos] <= '9':
                pos += 1
            self.pos = pos
            lexeme = input_str[start:pos]
            value = int(lexeme)
            if value > 2147483647:
                return Token(ERROR, lexeme, self.line)
            return Token(CONSTANT, lexeme, self.line, value)
        
        # Words (identifiers/keywords)
        if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
            start = pos
            while pos < length:
                c = input_str[pos]
                if not (('a' <= c <= 'z') or ('A' <= c <= 'Z') or ('0' <= c <= '9')):
                    break
                pos += 1
            
            self.pos = pos
            lexeme = input_str[start:pos]
            
            # Check register
            if lexeme[0] == 'r' and len(lexeme) > 1 and lexeme[1:].isdigit():
                return Token(REGISTER, lexeme, self.line, int(lexeme[1:]))
            
            # Check opcode
            token_type = self._opcodes.get(lexeme, ERROR)
            return Token(token_type, lexeme, self.line)
        
        # Unknown character
        self.pos = pos + 1
        return Token(ERROR, ch, self.line)
    
    def get_token_type_string(self, token):
        """Get string for token type"""
        return self._type_strings[token.type] if 0 <= token.type <= 16 else str(token.type)