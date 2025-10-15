"""
frontend.py - ILOC Front End Controller
Main controller class that coordinates scanner and parser
"""

import sys
from scanner import Scanner, TokenType, EOF, ENDLINE
from parser import Parser

class ILOCFrontEnd:
    """Main front end controller class"""
    
    def __init__(self, filename: str):
        """Initialize front end with input file"""
        self.filename = filename
        self.scanner = None
        self.parser = None
    
    def scan_only(self):
        """
        Mode -s: Print all tokens
        Scans the input and prints tokens to stdout
        """
        scanner = Scanner(self.filename)
        token = scanner.next_token()
        
        while token.type != TokenType.EOF:
            if token.type != TokenType.ENDLINE:
                type_str = scanner.get_token_type_string(token)
                print(f"{token.line}: {type_str} \"{token.lexeme}\"")
            token = scanner.next_token()
    
    def parse_only(self):
        """
        Mode -p: Parse and report success or errors
        Parses the input and reports whether it's valid ILOC
        """
        scanner = Scanner(self.filename)
        parser = Parser(scanner)
        success = parser.parse()
        
        if success:
            operation_count = parser.get_ir().get_operation_count()
            print(f"Parse succeeded. Processed {operation_count} operations.")
        else:
            print("Parse found errors.", file=sys.stderr)
            for error in parser.get_errors():
                print(error, file=sys.stderr)
    
    def print_ir(self):
        """
        Mode -r: Parse and print intermediate representation
        Parses the input and prints the IR in human-readable format
        """
        scanner = Scanner(self.filename)
        parser = Parser(scanner)
        success = parser.parse()
        
        if not success:
            for error in parser.get_errors():
                print(error, file=sys.stderr)
            return
        
        # Print the IR
        parser.get_ir().print_ir()
    
    @staticmethod
    def print_help():
        """Print help message for command-line usage"""
        print("COMP 412 Lab 1: ILOC Front End")
        print("Command line arguments:")
        print("  412fe -h           : Print this help message")
        print("  412fe -s <file>    : Scan and print tokens")
        print("  412fe -p <file>    : Parse and report errors (default)")
        print("  412fe -r <file>    : Parse and print intermediate representation")
        print("")
        print("If no flag is specified, -p is assumed.")
        print("Flags are mutually exclusive with priority: -h > -r > -p > -s")