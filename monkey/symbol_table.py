from typing import TypeAlias
from dataclasses import dataclass

SymbolScope: TypeAlias = str

GlobalScope:   SymbolScope = 'GLOBAL'
LocalScope:    SymbolScope = 'LOCAL'
BuiltinScope:  SymbolScope = 'BUILTIN'
FreeScope:     SymbolScope = 'FREE'
FunctionScope: SymbolScope = 'FUNCTION'


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
        self.free_symbols = []

    def define(self, name: str) -> Symbol:
        scope = GlobalScope if self.outer is None else LocalScope
        symbol = Symbol(name, scope, self.num_definitions)
        self.store[name] = symbol
        self.num_definitions += 1
        return symbol

    def define_builtin(self, index: int, name: str) -> Symbol:
        symbol = Symbol(name, BuiltinScope, index)
        self.store[name] = symbol
        return symbol

    def define_free(self, original: Symbol) -> Symbol:
        self.free_symbols.append(original)
        symbol = Symbol(name=original.name, scope=FreeScope, index=len(self.free_symbols)-1)
        self.store[original.name] = symbol
        return symbol 

    def define_function_name(self, name: str) -> Symbol:
        symbol = Symbol(name, FunctionScope, index=0)
        self.store[name] = symbol
        return symbol
    
    def resolve(self, name: str) -> Symbol | None:
        if name in self.store:
            return self.store[name]
        
        if self.outer is not None:
            obj = self.outer.resolve(name)
            
            if obj is None:
                return None
                        
            if obj.scope == GlobalScope or obj.scope == BuiltinScope:
                return obj

            free = self.define_free(obj)
            return free
        
        return None
