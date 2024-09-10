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
    
    return NULL


def _monkey_last(args):
    if len(args) != 1:
        return new_error(f'wrong number of arguments. got={len(args)}, want=1')

    arg = args[0]
    if type(arg) is not ArrayObject:
        return new_error(f'argument to "last" must be ARRAY, got {arg.objtype()}')

    length = len(arg.elements)
    if length > 0:
        return arg.elements[length-1]
    
    return NULL


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
    
    return NULL


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
    return NULL


builtins = {
    'len':   BuiltinObject(fn=_monkey_len),
    'first': BuiltinObject(fn=_monkey_first),
    'last':  BuiltinObject(fn=_monkey_last),
    'rest':  BuiltinObject(fn=_monkey_rest),
    'push':  BuiltinObject(fn=_monkey_push),
    'puts':  BuiltinObject(fn=_monkey_puts),
}



__all__ = ['builtins']