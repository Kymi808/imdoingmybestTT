"""
parser.py - ILOC Parser Module
"""

from scanner import Scanner, LOAD, LOADI, STORE, ADD, SUB, MULT, LSHIFT, RSHIFT, OUTPUT, NOP, REGISTER, CONSTANT, COMMA, ARROW, ENDLINE, EOF, ERROR
from ir import ILOCOperation, IRList

class Parser:
    """Simple ILOC Parser"""
    __slots__ = ['scanner', 'current_token', 'errors', 'ir_list']
    
    def __init__(self, scanner):
        self.scanner = scanner
        self.current_token = None
        self.errors = []
        self.ir_list = IRList()
    
    def parse(self):
        """Parse input file"""
        # Get first token
        self.current_token = self.scanner.next_token()
        
        # Cache methods for speed
        next_token = self.scanner.next_token
        append_error = self.errors.append
        append_op = self.ir_list.append
        
        # Main loop
        while self.current_token.type != EOF:
            token = self.current_token
            ttype = token.type
            
            # Skip empty lines
            if ttype == ENDLINE:
                self.current_token = next_token()
                continue
            
            line = token.line
            
            # Process operation based on type
            if ttype == LOADI:
                # loadI constant => register
                op = ILOCOperation(line, "loadI")
                
                self.current_token = next_token()
                if self.current_token.type != CONSTANT:
                    append_error(f"ERROR {line}: Expected constant after loadI")
                    self._skip_line()
                    continue
                op.sr1 = self.current_token.value
                
                self.current_token = next_token()
                if self.current_token.type != ARROW:
                    append_error(f"ERROR {line}: Expected '=>' after constant")
                    self._skip_line()
                    continue
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after '=>'")
                    self._skip_line()
                    continue
                op.sr3 = self.current_token.value
                append_op(op)
                
            elif ttype == LOAD or ttype == STORE:
                # load/store register => register
                opcode = "load" if ttype == LOAD else "store"
                op = ILOCOperation(line, opcode)
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after {opcode}")
                    self._skip_line()
                    continue
                op.sr1 = self.current_token.value
                
                self.current_token = next_token()
                if self.current_token.type != ARROW:
                    append_error(f"ERROR {line}: Expected '=>' after register")
                    self._skip_line()
                    continue
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after '=>'")
                    self._skip_line()
                    continue
                op.sr3 = self.current_token.value
                append_op(op)
                
            elif ttype >= ADD and ttype <= RSHIFT:
                # Arithmetic operations
                opcode = token.lexeme
                op = ILOCOperation(line, opcode)
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after {opcode}")
                    self._skip_line()
                    continue
                op.sr1 = self.current_token.value
                
                self.current_token = next_token()
                if self.current_token.type != COMMA:
                    append_error(f"ERROR {line}: Expected ',' after first register")
                    self._skip_line()
                    continue
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after ','")
                    self._skip_line()
                    continue
                op.sr2 = self.current_token.value
                
                self.current_token = next_token()
                if self.current_token.type != ARROW:
                    append_error(f"ERROR {line}: Expected '=>' after second register")
                    self._skip_line()
                    continue
                
                self.current_token = next_token()
                if self.current_token.type != REGISTER:
                    append_error(f"ERROR {line}: Expected register after '=>'")
                    self._skip_line()
                    continue
                op.sr3 = self.current_token.value
                append_op(op)
                
            elif ttype == OUTPUT:
                # output constant
                op = ILOCOperation(line, "output")
                
                self.current_token = next_token()
                if self.current_token.type != CONSTANT:
                    append_error(f"ERROR {line}: Expected constant after output")
                    self._skip_line()
                    continue
                op.sr1 = self.current_token.value
                append_op(op)
                
            elif ttype == NOP:
                # nop
                append_op(ILOCOperation(line, "nop"))
                
            else:
                # Invalid opcode
                append_error(f"ERROR {line}: Invalid opcode: {token.lexeme}")
                self._skip_line()
                continue
            
            # Move to next token
            self.current_token = next_token()
            if self.current_token.type not in (ENDLINE, EOF):
                append_error(f"ERROR {line}: Unexpected token after operation: {self.current_token.lexeme}")
                self._skip_line()
        
        return len(self.errors) == 0
    
    def _skip_line(self):
        """Skip to next line"""
        next_token = self.scanner.next_token
        while self.current_token.type not in (ENDLINE, EOF):
            self.current_token = next_token()
        if self.current_token.type == ENDLINE:
            self.current_token = next_token()
    
    def get_errors(self):
        return self.errors
    
    def get_ir(self):
        return self.ir_list