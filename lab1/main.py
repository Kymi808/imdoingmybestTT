"""
main.py - Main Entry Point for ILOC Front End
COMP 412 Lab 1
Handles command-line argument parsing and mode selection
"""

import sys
import os
from frontend import ILOCFrontEnd

def parse_arguments():
    """
    Parse command-line arguments and return mode and filename.
    Priority order: -h > -r > -p > -s
    Default mode is -p if no flag specified.
    """
    # Check for help flag first 
    if "-h" in sys.argv:
        return "-h", None
    
    # Initialize defaults
    mode = "-p"  
    filename = None
    
    # Check for other flags in priority order
    if "-r" in sys.argv:
        mode = "-r"
        idx = sys.argv.index("-r")
        if idx + 1 < len(sys.argv):
            filename = sys.argv[idx + 1]
    elif "-p" in sys.argv:
        mode = "-p"
        idx = sys.argv.index("-p")
        if idx + 1 < len(sys.argv):
            filename = sys.argv[idx + 1]
    elif "-s" in sys.argv:
        mode = "-s"
        idx = sys.argv.index("-s")
        if idx + 1 < len(sys.argv):
            filename = sys.argv[idx + 1]
    else:
        # No flag specified, last argument is filename
        if len(sys.argv) > 1:
            filename = sys.argv[-1]
    
    return mode, filename

def validate_file(filename):
    if not filename:
        print("ERROR: No input file specified", file=sys.stderr)
        ILOCFrontEnd.print_help()
        sys.exit(1)
    
    if not os.path.exists(filename):
        print(f"ERROR: Cannot read file '{filename}'", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isfile(filename):
        print(f"ERROR: '{filename}' is not a file", file=sys.stderr)
        sys.exit(1)

def main():
    """Main entry point for the ILOC front end"""
    
    # Check minimum arguments
    if len(sys.argv) < 2:
        print("ERROR: No input file specified", file=sys.stderr)
        ILOCFrontEnd.print_help()
        sys.exit(1)
    
    # Parse command-line arguments
    mode, filename = parse_arguments()
    
    # Handle help mode
    if mode == "-h":
        ILOCFrontEnd.print_help()
        sys.exit(0)
    
    # Validate input file
    validate_file(filename)
    
    # Create front end and execute appropriate mode
    try:
        frontend = ILOCFrontEnd(filename)
        
        if mode == "-s":
            frontend.scan_only()
        elif mode == "-p":
            frontend.parse_only()
        elif mode == "-r":
            frontend.print_ir()
            
    except Exception as e:
        # Catch any unexpected errors to ensure graceful termination
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()