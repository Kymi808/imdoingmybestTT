
"""
Debug script to test where the timeout is happening
"""

import sys
import time

def test_scanner():
    """Test just the scanner"""
    print("Testing scanner...")
    start = time.time()
    
    # Create a simple test file
    with open('test_simple.i', 'w') as f:
        f.write("loadI 1 => r1\n")
        f.write("add r1, r1 => r2\n")
        f.write("output 1024\n")
    
    try:
        from scanner import Scanner, TokenType
        scanner = Scanner('test_simple.i')
        
        count = 0
        token = scanner.next_token()
        while token.type != TokenType.EOF:
            print(f"Token {count}: {token.type} - {token.lexeme}")
            token = scanner.next_token()
            count += 1
            if count > 100:  # Safety check
                print("ERROR: Too many tokens, possible infinite loop")
                break
        
        print(f"Scanner test completed in {time.time() - start:.3f} seconds")
        return True
    except Exception as e:
        print(f"Scanner test failed: {e}")
        return False

def test_parser():
    """Test the parser"""
    print("\nTesting parser...")
    start = time.time()
    
    try:
        from scanner import Scanner
        from parser import Parser
        
        scanner = Scanner('test_simple.i')
        parser = Parser(scanner)
        
        success = parser.parse()
        
        if success:
            print(f"Parse succeeded with {parser.get_ir().get_operation_count()} operations")
        else:
            print("Parse failed with errors:")
            for error in parser.get_errors():
                print(f"  {error}")
        
        print(f"Parser test completed in {time.time() - start:.3f} seconds")
        return True
    except Exception as e:
        print(f"Parser test failed: {e}")
        return False

def test_main():
    """Test the main entry point"""
    print("\nTesting main program...")
    start = time.time()
    
    try:
        import subprocess
        result = subprocess.run(['python3', 'main.py', '-p', 'test_simple.i'], 
                              capture_output=True, text=True, timeout=5)
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        print(f"Main test completed in {time.time() - start:.3f} seconds")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("ERROR: Main program timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"Main test failed: {e}")
        return False

if __name__ == "__main__":
    print("Debug test for ILOC front end")
    print("=" * 40)
    
    # Test each component
    scanner_ok = test_scanner()
    
    if scanner_ok:
        parser_ok = test_parser()
        
        if parser_ok:
            main_ok = test_main()
        else:
            print("\nParser has issues, skipping main test")
    else:
        print("\nScanner has issues, skipping further tests")