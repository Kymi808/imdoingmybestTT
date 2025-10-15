#!/usr/bin/env python3
"""
412alloc.py - Lab 2 Register Allocator
"""

import sys
import os
from scanner import Scanner
from parser import Parser

def rename_registers(ir_list):
    """Perform register renaming"""
    next_vr = 0
    sr_to_vr = {}
    max_vr = 0
    
    for op in ir_list.iterate_forward():
        # Handle uses first (before definitions)
        if op.opcode in ["load", "store"]:
            if op.sr1 >= 0:
                if op.sr1 in sr_to_vr:
                    op.vr1 = sr_to_vr[op.sr1]
                else:
                    op.vr1 = next_vr
                    sr_to_vr[op.sr1] = next_vr
                    max_vr = max(max_vr, next_vr)
                    next_vr += 1
            
            if op.opcode == "store" and op.sr3 >= 0:
                if op.sr3 in sr_to_vr:
                    op.vr3 = sr_to_vr[op.sr3]
                else:
                    op.vr3 = next_vr
                    sr_to_vr[op.sr3] = next_vr
                    max_vr = max(max_vr, next_vr)
                    next_vr += 1
                    
        elif op.opcode in ["add", "sub", "mult", "lshift", "rshift"]:
            if op.sr1 >= 0:
                if op.sr1 in sr_to_vr:
                    op.vr1 = sr_to_vr[op.sr1]
                else:
                    op.vr1 = next_vr
                    sr_to_vr[op.sr1] = next_vr
                    max_vr = max(max_vr, next_vr)
                    next_vr += 1
                    
            if op.sr2 >= 0:
                if op.sr2 in sr_to_vr:
                    op.vr2 = sr_to_vr[op.sr2]
                else:
                    op.vr2 = next_vr
                    sr_to_vr[op.sr2] = next_vr
                    max_vr = max(max_vr, next_vr)
                    next_vr += 1
        
        # Handle definitions
        if op.opcode == "loadI" and op.sr3 >= 0:
            op.vr3 = next_vr
            sr_to_vr[op.sr3] = next_vr
            max_vr = max(max_vr, next_vr)
            next_vr += 1
                
        elif op.opcode == "load" and op.sr3 >= 0:
            op.vr3 = next_vr
            sr_to_vr[op.sr3] = next_vr
            max_vr = max(max_vr, next_vr)
            next_vr += 1
                
        elif op.opcode in ["add", "sub", "mult", "lshift", "rshift"] and op.sr3 >= 0:
            op.vr3 = next_vr
            sr_to_vr[op.sr3] = next_vr
            max_vr = max(max_vr, next_vr)
            next_vr += 1
    
    # Compute next use
    vr_next = {}
    for op in ir_list.iterate_backward():
        # Handle definitions - kill live range
        if op.opcode in ["loadI", "load", "add", "sub", "mult", "lshift", "rshift"]:
            if op.vr3 >= 0:
                if op.vr3 in vr_next:
                    op.nu3 = vr_next[op.vr3]
                else:
                    op.nu3 = float('inf')
                vr_next.pop(op.vr3, None)
        
        # Handle uses - extend live range
        if op.opcode in ["load", "store"]:
            if op.vr1 >= 0:
                if op.vr1 in vr_next:
                    op.nu1 = vr_next[op.vr1]
                else:
                    op.nu1 = float('inf')
                vr_next[op.vr1] = op.line
            
            if op.opcode == "store" and op.vr3 >= 0:
                if op.vr3 in vr_next:
                    op.nu3 = vr_next[op.vr3]
                else:
                    op.nu3 = float('inf')
                vr_next[op.vr3] = op.line
                
        elif op.opcode in ["add", "sub", "mult", "lshift", "rshift"]:
            if op.vr1 >= 0:
                if op.vr1 in vr_next:
                    op.nu1 = vr_next[op.vr1]
                else:
                    op.nu1 = float('inf')
                vr_next[op.vr1] = op.line
                
            if op.vr2 >= 0:
                if op.vr2 in vr_next:
                    op.nu2 = vr_next[op.vr2]
                else:
                    op.nu2 = float('inf')
                vr_next[op.vr2] = op.line
    
    return max_vr + 1


def allocate(ir_list, k):
    """Perform register allocation with k registers"""
    # Reserve last register for spilling
    spill_reg = k - 1
    num_regs = k - 1
    
    pr_to_vr = [None] * num_regs
    vr_to_pr = {}
    vr_nu = {}
    vr_spilled = {}
    vr_loadI = {}  # Track loadI constants for rematerialization
    
    next_spill = 32768
    
    for op in ir_list.iterate_forward():
        # Handle loadI specially - mark for rematerialization
        if op.opcode == "loadI":
            vr3 = op.vr3 if op.vr3 >= 0 else None
            if vr3 is not None:
                vr_loadI[vr3] = op.sr1  # Store the constant value
                vr_nu[vr3] = op.nu3
            continue  # Don't allocate a register yet
        
        # Get virtual registers
        vr1 = op.vr1 if op.vr1 >= 0 else None
        vr2 = op.vr2 if op.vr2 >= 0 else None
        vr3 = op.vr3 if op.vr3 >= 0 else None
        
        # For store, vr3 is a use, not a def
        if op.opcode == "store":
            vr3_use = vr3
            vr3 = None
        else:
            vr3_use = None
        
        # Process first operand (vr1)
        if vr1 is not None:
            if vr1 not in vr_to_pr:
                pr = get_pr(pr_to_vr, vr_nu, num_regs)
                
                # Spill if needed
                if pr_to_vr[pr] is not None:
                    old_vr = pr_to_vr[pr]
                    # Don't spill if it's a loadI value (can rematerialize)
                    if old_vr not in vr_loadI and old_vr not in vr_spilled:
                        vr_spilled[old_vr] = next_spill
                        next_spill += 4
                        print(f"loadI {vr_spilled[old_vr]} => r{spill_reg}")
                        print(f"store r{pr} => r{spill_reg}")
                    del vr_to_pr[old_vr]
                    pr_to_vr[pr] = None
                
                # Restore or rematerialize
                if vr1 in vr_loadI:
                    # Rematerialize loadI
                    print(f"loadI {vr_loadI[vr1]} => r{pr}")
                elif vr1 in vr_spilled:
                    # Restore from memory
                    print(f"loadI {vr_spilled[vr1]} => r{spill_reg}")
                    print(f"load r{spill_reg} => r{pr}")
                
                vr_to_pr[vr1] = pr
                pr_to_vr[pr] = vr1
            
            op.pr1 = vr_to_pr[vr1]
            vr_nu[vr1] = op.nu1
        
        # Process second operand (vr2)
        if vr2 is not None:
            if vr2 not in vr_to_pr:
                pr = get_pr(pr_to_vr, vr_nu, num_regs)
                
                if pr_to_vr[pr] is not None:
                    old_vr = pr_to_vr[pr]
                    if old_vr not in vr_loadI and old_vr not in vr_spilled:
                        vr_spilled[old_vr] = next_spill
                        next_spill += 4
                        print(f"loadI {vr_spilled[old_vr]} => r{spill_reg}")
                        print(f"store r{pr} => r{spill_reg}")
                    del vr_to_pr[old_vr]
                    pr_to_vr[pr] = None
                
                if vr2 in vr_loadI:
                    print(f"loadI {vr_loadI[vr2]} => r{pr}")
                elif vr2 in vr_spilled:
                    print(f"loadI {vr_spilled[vr2]} => r{spill_reg}")
                    print(f"load r{spill_reg} => r{pr}")
                
                vr_to_pr[vr2] = pr
                pr_to_vr[pr] = vr2
            
            op.pr2 = vr_to_pr[vr2]
            vr_nu[vr2] = op.nu2
        
        # Process store's third operand as use
        if vr3_use is not None:
            if vr3_use not in vr_to_pr:
                pr = get_pr(pr_to_vr, vr_nu, num_regs)
                
                if pr_to_vr[pr] is not None:
                    old_vr = pr_to_vr[pr]
                    if old_vr not in vr_loadI and old_vr not in vr_spilled:
                        vr_spilled[old_vr] = next_spill
                        next_spill += 4
                        print(f"loadI {vr_spilled[old_vr]} => r{spill_reg}")
                        print(f"store r{pr} => r{spill_reg}")
                    del vr_to_pr[old_vr]
                    pr_to_vr[pr] = None
                
                if vr3_use in vr_loadI:
                    print(f"loadI {vr_loadI[vr3_use]} => r{pr}")
                elif vr3_use in vr_spilled:
                    print(f"loadI {vr_spilled[vr3_use]} => r{spill_reg}")
                    print(f"load r{spill_reg} => r{pr}")
                
                vr_to_pr[vr3_use] = pr
                pr_to_vr[pr] = vr3_use
            
            op.pr3 = vr_to_pr[vr3_use]
            vr_nu[vr3_use] = op.nu3
        
        # Free values that are dead after use
        if vr1 is not None and op.nu1 == float('inf'):
            if vr1 in vr_to_pr:
                pr = vr_to_pr[vr1]
                del vr_to_pr[vr1]
                pr_to_vr[pr] = None
        
        if vr2 is not None and op.nu2 == float('inf'):
            if vr2 in vr_to_pr:
                pr = vr_to_pr[vr2]
                del vr_to_pr[vr2]
                pr_to_vr[pr] = None
        
        if vr3_use is not None and op.nu3 == float('inf'):
            if vr3_use in vr_to_pr:
                pr = vr_to_pr[vr3_use]
                del vr_to_pr[vr3_use]
                pr_to_vr[pr] = None
        
        # Handle definition
        if vr3 is not None:
            if vr3 in vr_loadI:
                del vr_loadI[vr3]
            
            pr = get_pr(pr_to_vr, vr_nu, num_regs)
            
            if pr_to_vr[pr] is not None:
                old_vr = pr_to_vr[pr]
                if old_vr not in vr_loadI and old_vr not in vr_spilled:
                    vr_spilled[old_vr] = next_spill
                    next_spill += 4
                    print(f"loadI {vr_spilled[old_vr]} => r{spill_reg}")
                    print(f"store r{pr} => r{spill_reg}")
                del vr_to_pr[old_vr]
                pr_to_vr[pr] = None
            
            vr_to_pr[vr3] = pr
            pr_to_vr[pr] = vr3
            op.pr3 = pr
            vr_nu[vr3] = op.nu3
            
            # Free if dead immediately
            if op.nu3 == float('inf'):
                del vr_to_pr[vr3]
                pr_to_vr[pr] = None
        
        # Print the allocated operation
        if op.opcode == "load":
            print(f"load r{op.pr1} => r{op.pr3}")
        elif op.opcode == "store":
            print(f"store r{op.pr1} => r{op.pr3}")
        elif op.opcode in ["add", "sub", "mult", "lshift", "rshift"]:
            print(f"{op.opcode} r{op.pr1}, r{op.pr2} => r{op.pr3}")
        elif op.opcode == "output":
            print(f"output {op.sr1}")
        elif op.opcode == "nop":
            print("nop")


def get_pr(pr_to_vr, vr_nu, num_regs):
    """Get a physical register using furthest next use heuristic"""
    # First, look for a free register
    for pr in range(num_regs):
        if pr_to_vr[pr] is None:
            return pr
    
    # No free register, find the one with furthest next use
    best_pr = 0
    best_nu = 0
    
    for pr in range(num_regs):
        vr = pr_to_vr[pr]
        if vr is not None:
            nu = vr_nu.get(vr, float('inf'))
            if nu > best_nu or (nu == best_nu and pr < best_pr):
                best_pr = pr
                best_nu = nu
    
    return best_pr

def print_renamed(ir_list):
    """Print renamed ILOC"""
    for op in ir_list.iterate_forward():
        if op.opcode == "loadI":
            print(f"loadI {op.sr1} => r{op.vr3}")
        elif op.opcode == "load":
            print(f"load r{op.vr1} => r{op.vr3}")
        elif op.opcode == "store":
            print(f"store r{op.vr1} => r{op.vr3}")
        elif op.opcode in ["add", "sub", "mult", "lshift", "rshift"]:
            print(f"{op.opcode} r{op.vr1}, r{op.vr2} => r{op.vr3}")
        elif op.opcode == "output":
            print(f"output {op.sr1}")
        elif op.opcode == "nop":
            print("nop")

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    if sys.argv[1] == "-h":
        print("Usage: 412alloc k filename")
        print("       412alloc -x filename")
        print("       412alloc -h")
        sys.exit(0)
    
    elif sys.argv[1] == "-x":
        if len(sys.argv) != 3:
            sys.exit(1)
        
        filename = sys.argv[2]
        if not os.path.exists(filename):
            sys.exit(1)
        
        scanner = Scanner(filename)
        parser = Parser(scanner)
        if not parser.parse():
            sys.exit(1)
        
        ir_list = parser.get_ir()
        rename_registers(ir_list)
        print_renamed(ir_list)
    
    else:
        # k filename format
        try:
            k = int(sys.argv[1])
            if k < 3 or k > 64:
                sys.exit(1)
            
            if len(sys.argv) != 3:
                sys.exit(1)
            
            filename = sys.argv[2]
            if not os.path.exists(filename):
                sys.exit(1)
            
            scanner = Scanner(filename)
            parser = Parser(scanner)
            if not parser.parse():
                sys.exit(1)
            
            ir_list = parser.get_ir()
            rename_registers(ir_list)
            allocate(ir_list, k)
            
        except ValueError:
            sys.exit(1)

if __name__ == "__main__":
    main()