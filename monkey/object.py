from dataclasses import dataclass
from enum import Enum
from abc import abstractmethod
from typing import Any, Callable

from monkey import myast as ast
from monkey import code

class ObjectType(Enum):
    BOOLEAN_OBJ           = 'BOOLEAN'
    INTEGER_OBJ           = 'INTEGER'
    STRING_OBJ            = 'STRING'
    RETURN_VALUE_OBJ      = 'RETURN_VALUE'
    FUNCTION_OBJ          = 'FUNCTION'
    COMPILED_FUNCTION_OBJ = 'COMPILED_FUNCTION'
    ARRAY_OBJ             = 'ARRAY'
    HASH_OBJ              = 'HASH'
    BUILTIN_OBJ           = 'BUILTIN'
    QUOTE_OBJ             = 'QUOTE'
    NULL_OBJ              = 'NULL'
    ERROR_OBJ             = 'ERROR'



@dataclass
class Object:
    @abstractmethod
    def objtype(self) -> ObjectType:
        raise NotImplementedError

    @abstractmethod
    def inspect(self) -> str:
        raise NotImplementedError


@dataclass
class IntegerObject(Object):
    value: int

    def objtype(self):
        return ObjectType.INTEGER_OBJ

    def inspect(self):
        return f'{self.value}'

    def __hash__(self):
        return hash(self.value)

@dataclass
class StringObject(Object):
    value: str

    def objtype(self):
        return ObjectType.STRING_OBJ

    def inspect(self):
        return self.value

    def __hash__(self):
        return hash(self.value)


@dataclass
class BooleanObject(Object):
    value: bool

    def objtype(self):
        return ObjectType.BOOLEAN_OBJ

    def inspect(self):
        return f'{self.value}'

    def __hash__(self):
        return hash(self.value)

@dataclass
class ReturnValue(Object):
    value: Object

    def objtype(self):
        return ObjectType.RETURN_VALUE_OBJ

    def inspect(self):
        return self.value.inspect()


@dataclass
class FunctionObject(Object):
    parameters: list[ast.Identifier]
    body: ast.BlockStatement
    env: Any # This is really Environment but python yalps

    def objtype(self):
        return ObjectType.FUNCTION_OBJ
    
    def inspect(self):
        params = ', '.join([str(p) for p in self.parameters])
        return f'fn({params}) ' + '{' + f'\n{self.body}\n' + '}'


@dataclass
class CompiledFunction(Object):
    instructions: code.Instructions
    num_locals: int = 0
    num_parameters: int = 0

    def objtype(self):
        return ObjectType.COMPILED_FUNCTION_OBJ
    
    def inspect(self):
        return f'CompiledFunction[{id(self)}]'


@dataclass
class ArrayObject(Object):
    # We use a python tuple because monkey arrays are immutable
    # and can hold multiple data types at once
    elements: tuple[Object]

    def objtype(self):
        return ObjectType.ARRAY_OBJ
    
    def inspect(self):
        elements = ', '.join([str(e.inspect()) for e in self.elements])
        return f'[{elements}]' 

@dataclass
class HashObject(Object):
    pairs: dict[Object, Object]

    def objtype(self):
        return ObjectType.HASH_OBJ
    
    def inspect(self):
        pairs = ', '.join([f'{k.inspect()}:{v.inspect()}' for k, v in self.pairs.items()])
        return '{' + pairs + '}'

@dataclass
class BuiltinObject(Object):
    fn: Callable

    def objtype(self):
        return ObjectType.BUILTIN_OBJ
    
    def inspect(self):
        return 'builtin function'


@dataclass
class QuoteObject(Object):
    node: ast.Node

    def objtype(self):
        return ObjectType.QUOTE_OBJ
    
    def inspect(self):
        return f'QUOTE({self.node})'

        
@dataclass
class NullObject(Object):
    def objtype(self):
        return ObjectType.NULL_OBJ

    def inspect(self):
        return 'null'


@dataclass
class ErrorObject(Object):
    message: str

    def objtype(self):
        return ObjectType.ERROR_OBJ

    def inspect(self):
        return f'ERROR: {self.message}'



def new_error(message: str) -> ErrorObject:
    return ErrorObject(message)

def is_error(obj: Object) -> bool:
    return obj is not None and obj.objtype() == ObjectType.ERROR_OBJ



class Environment:
    def __init__(self, outer=None):
        self.store = {}
        self.outer = outer
    
    def get(self, name: str) -> Object:
        if name in self.store:
            return self.store.get(name)
        elif self.outer is not None:
            return self.outer.get(name)
        else:
            return None
    
    def set(self, name: str, thing: Object):
        self.store[name] = thing

NULL  = NullObject()
TRUE  = BooleanObject(value=True)
FALSE = BooleanObject(value=False)