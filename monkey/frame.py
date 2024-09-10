from monkey import code
from monkey.object import *


class Frame:
    def __init__(self, fn: CompiledFunction):
        self.fn = fn
        self.ip = -1
    
    @property
    def instructions(self):
        return self.fn.instructions

