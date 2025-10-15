"""
ir.py - Intermediate Representation
"""

class ILOCOperation:
    """Single ILOC operation"""
    __slots__ = ['line', 'opcode', 'sr1', 'vr1', 'pr1', 'nu1',
                 'sr2', 'vr2', 'pr2', 'nu2', 'sr3', 'vr3', 'pr3', 'nu3',
                 'next', 'prev']
    
    def __init__(self, line=0, opcode=''):
        self.line = line
        self.opcode = opcode
        self.sr1 = -1
        self.vr1 = -1
        self.pr1 = -1
        self.nu1 = -1
        self.sr2 = -1
        self.vr2 = -1
        self.pr2 = -1
        self.nu2 = -1
        self.sr3 = -1
        self.vr3 = -1
        self.pr3 = -1
        self.nu3 = -1
        self.next = None
        self.prev = None
    
    def print_human_readable(self):
        """Print operation in human-readable format"""
        op = self.opcode
        s1, s2, s3 = self.sr1, self.sr2, self.sr3
        
        if op == "loadI":
            print(f"[ {'loadI':8s} | val: {s1:6d} |        -       | r{s3:6d} | ]")
        elif op in ("load", "store"):
            print(f"[ {op:8s} | r{s1:6d} |        -       | r{s3:6d} | ]")
        elif op in ("add", "sub", "mult", "lshift", "rshift"):
            print(f"[ {op:8s} | r{s1:6d} | r{s2:6d} | r{s3:6d} | ]")
        elif op == "output":
            print(f"[ {'output':8s} | val: {s1:6d} |        -       |        -       | ]")
        elif op == "nop":
            print(f"[ {'nop':8s} |        -       |        -       |        -       | ]")


class IRList:
    """Doubly-linked list of ILOC operations"""
    __slots__ = ['head', 'tail', 'count']
    
    def __init__(self):
        self.head = None
        self.tail = None
        self.count = 0
    
    def append(self, operation):
        """Add operation to end of list"""
        if not self.head:
            self.head = operation
            self.tail = operation
        else:
            self.tail.next = operation
            operation.prev = self.tail
            self.tail = operation
        self.count += 1
    
    def print_ir(self):
        """Print entire IR"""
        current = self.head
        while current:
            current.print_human_readable()
            current = current.next
    
    def get_operation_count(self):
        return self.count
    
    def iterate_forward(self):
        """Generator for forward iteration"""
        current = self.head
        while current:
            yield current
            current = current.next
    
    def iterate_backward(self):
        """Generator for backward iteration"""
        current = self.tail
        while current:
            yield current
            current = current.prev