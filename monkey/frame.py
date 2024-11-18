from monkey.object import *


class Frame:
    def __init__(self, cl: ClosureObject, base_pointer: int):
        self.cl = cl
        self.ip = -1
        self.base_pointer = base_pointer
    
    @property
    def instructions(self):
        return self.cl.fn.instructions
