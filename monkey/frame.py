from monkey import code
from monkey.object import *


class Frame:
    def __init__(self, fn: CompiledFunction, base_pointer: int):
        self.fn = fn
        self.ip = -1
        self.base_pointer = base_pointer
    
    @property
    def instructions(self):
        return self.fn.instructions

