from typing import TypeAlias
from dataclasses import dataclass

SymbolScope: TypeAlias = str

GlobalScope: SymbolScope = 'GLOBAL'


@dataclass
class Symbol:  
    name: str
    scope: SymbolScope
    index: int
    

class SymbolTable:
    def __init__(self):
        self.store = {}
        self.num_definitions = 0

    def define(self, name: str) -> Symbol:
        symbol = Symbol(name, GlobalScope, self.num_definitions)
        self.store[name] = symbol
        self.num_definitions += 1
        return symbol
    
    def resolve(self, name: str) -> Symbol | None:
        return self.store.get(name, None)