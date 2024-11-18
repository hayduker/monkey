from collections import namedtuple
from monkey.object import *


def _monkey_len(args):
    if len(args) != 1:
        return new_error(f'wrong number of arguments. got={len(args)}, want=1')

    arg = args[0]
    if type(arg) is StringObject:
        return IntegerObject(value=len(arg.value)) # use Python builtin "len"
    elif type(arg) is ArrayObject:
        return IntegerObject(value=len(arg.elements))
    else:
        return new_error(f'argument to "len" not supported, got {arg.objtype()}')


def _monkey_first(args):
    if len(args) != 1:
        return new_error(f'wrong number of arguments. got={len(args)}, want=1')

    arg = args[0]
    if type(arg) is not ArrayObject:
        return new_error(f'argument to "first" must be ARRAY, got {arg.objtype()}')

    if len(arg.elements) > 0:
        return arg.elements[0]
    
    return None


def _monkey_last(args):
    if len(args) != 1:
        return new_error(f'wrong number of arguments. got={len(args)}, want=1')

    arg = args[0]
    if type(arg) is not ArrayObject:
        return new_error(f'argument to "last" must be ARRAY, got {arg.objtype()}')

    length = len(arg.elements)
    if length > 0:
        return arg.elements[length-1]
    
    return None


def _monkey_rest(args):
    if len(args) != 1:
        return new_error(f'wrong number of arguments. got={len(args)}, want=1')

    arg = args[0]
    if type(arg) is not ArrayObject:
        return new_error(f'argument to "rest" must be ARRAY, got {arg.objtype()}')

    length = len(arg.elements)
    if length > 0:
        new_elements = arg.elements[1:]
        return ArrayObject(elements=new_elements)
    
    return None


def _monkey_push(args):
    if len(args) != 2:
        return new_error(f'wrong number of arguments. got={len(args)}, want=2')

    array = args[0]
    new_element = args[1]
    if type(array) is not ArrayObject:
        return new_error(f'argument to "push" must be ARRAY, got {array.objtype()}')

    length = len(array.elements)
    new_elements = array.elements + [new_element]
    return ArrayObject(elements=new_elements)


def _monkey_puts(args):
    string = '\n'.join([a.inspect() for a in args])
    print(string)
    return None



NamedBuiltin = namedtuple('NamedBuiltin', ['name', 'builtin'])

builtins = [
    NamedBuiltin('len',   BuiltinObject(fn=_monkey_len)),
    NamedBuiltin('puts',  BuiltinObject(fn=_monkey_puts)),
    NamedBuiltin('first', BuiltinObject(fn=_monkey_first)),
    NamedBuiltin('last',  BuiltinObject(fn=_monkey_last)),
    NamedBuiltin('rest',  BuiltinObject(fn=_monkey_rest)),
    NamedBuiltin('push',  BuiltinObject(fn=_monkey_push)),
]

def get_builtin_by_name(name):
    for nb in builtins:
        if nb.name == name:
            return nb.builtin
    
    return None


__all__ = ['builtins']