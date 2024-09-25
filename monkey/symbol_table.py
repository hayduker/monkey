from typing import TypeAlias
from dataclasses import dataclass

SymbolScope: TypeAlias = str

GlobalScope: SymbolScope = 'GLOBAL'
LocalScope:  SymbolScope = 'LOCAL'


@dataclass
class Symbol:  
    name: str
    scope: SymbolScope
    index: int
    

class SymbolTable:
    def __init__(self, outer=None):
        self.outer = outer
        self.store = {}
        self.num_definitions = 0

    def define(self, name: str) -> Symbol:
        scope = GlobalScope if self.outer is None else LocalScope
        symbol = Symbol(name, scope, self.num_definitions)
        self.store[name] = symbol
        self.num_definitions += 1
        return symbol
    
    def resolve(self, name: str) -> Symbol | None:
        if name in self.store:
            return self.store[name]
        
        if self.outer is not None:
            return self.outer.resolve(name)
        
        return None
