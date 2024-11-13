from monkey.code import Opcode
from monkey.compiler import Bytecode
from monkey.object import *
from monkey.frame import Frame

from typing import List


STACK_SIZE = 2048
GLOBALS_SIZE = 65536
MAX_FRAMES = 1024

TRUE = BooleanObject(True)
FALSE = BooleanObject(False)
NULL = NullObject()


class VmError(Exception):
    pass

class VirtualMachine:
    def __init__(self, bytecode: Bytecode):
        self.constants = bytecode.constants
        self.globals = [None] * GLOBALS_SIZE
        self.stack = [None] * STACK_SIZE
        # Always points to the next value. Top of stack is stack[sp-1]
        self.sp = 0

        self.frames = [None] * MAX_FRAMES
        main_fn = CompiledFunction(instructions=bytecode.instructions)
        main_frame = Frame(fn=main_fn, base_pointer=0)
        self.frames[0] = main_frame
        self.frames_index = 1

    def run(self) -> VmError | None:
        while self.current_frame.ip < len(self.current_frame.instructions) - 1:
            self.current_frame.ip += 1

            ip = self.current_frame.ip
            ins = self.current_frame.instructions
            op = Opcode(ins[ip].to_bytes(1))

            if op == Opcode.OpConstant:
                const_index = int.from_bytes(ins[ip+1:ip+3], 'big')
                self.current_frame.ip += 2

                err = self.push(self.constants[const_index])
                if err is not None:
                    return err
            
            elif op == Opcode.OpTrue:
                err = self.push(TRUE)
                if err is not None:
                    return err
            
            elif op == Opcode.OpFalse:
                err = self.push(FALSE)
                if err is not None:
                    return err
            
            elif op == Opcode.OpPop:
                self.pop()
            
            elif op in [Opcode.OpAdd, Opcode.OpSub, Opcode.OpMul, Opcode.OpDiv]:
                err = self.execute_binary_operation(op)
                if err is not None:
                    return err
            
            elif op in [Opcode.OpEqual, Opcode.OpNotEqual, Opcode.OpGreaterThan]:
                err = self.execute_comparison(op)
                if err is not None:
                    return err
            
            elif op == Opcode.OpBang:
                err = self.execute_bang_operator()
                if err is not None:
                    return err
            
            elif op == Opcode.OpMinus:
                err = self.execute_minus_operator()
                if err is not None:
                    return err
            
            elif op == Opcode.OpJump:
                pos = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip = pos - 1
            
            elif op == Opcode.OpJumpNotTruthy:
                pos = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip += 2

                condition = self.pop()
                if not self.is_truthy(condition):
                    self.current_frame.ip = pos - 1
            
            elif op == Opcode.OpNull:
                err = self.push(NULL)
                if err is not None:
                    return err
            
            elif op == Opcode.OpSetGlobal:
                global_index = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip += 2

                self.globals[global_index] = self.pop()
            
            elif op == Opcode.OpGetGlobal:
                global_index = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip += 2

                err = self.push(self.globals[global_index])
                if err is not None:
                    return err
            
            elif op == Opcode.OpArray:
                num_elements = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip += 2

                array = self.build_array(self.sp - num_elements, self.sp)
                self.sp -= num_elements

                err = self.push(array)
                if err is not None:
                    return err
            
            elif op == Opcode.OpHash:
                num_elements = int.from_bytes(ins[ip+1:ip+3])
                self.current_frame.ip += 2

                hash_map = self.build_hash(self.sp - num_elements, self.sp)
                self.sp -= num_elements

                err = self.push(hash_map)
                if err is not None:
                    return err

            elif op == Opcode.OpIndex:
                index = self.pop()
                left = self.pop()

                err = self.execute_index_expression(left, index)
                if err is not None:
                    return err

            elif op == Opcode.OpCall:
                num_args = int(ins[ip+1])
                self.current_frame.ip += 1

                err = self.call_function(num_args)
                if err is not None:
                    return err
            
            elif op == Opcode.OpReturnValue:
                return_value = self.pop()

                frame = self.pop_frame()
                self.sp = frame.base_pointer - 1

                err = self.push(return_value)
                if err is not None:
                    return err

            elif op == Opcode.OpReturn:
                frame = self.pop_frame()
                self.sp = frame.base_pointer - 1

                err = self.push(NULL)
                if err is not None:
                    return err
            
            elif op == Opcode.OpSetLocal:
                local_index = code.read_uint8(ins[ip+1:ip+2])
                self.current_frame.ip += 1

                frame = self.current_frame

                self.stack[frame.base_pointer + local_index] = self.pop()
            
            elif op == Opcode.OpGetLocal:
                local_index = code.read_uint8(ins[ip+1:ip+2])
                self.current_frame.ip += 1

                frame = self.current_frame

                err = self.push(self.stack[frame.base_pointer + local_index])
                if err is not None:
                    return err

    @property
    def current_frame(self) -> Frame:
        return self.frames[self.frames_index - 1]

    def push_frame(self, f: Frame) -> None:
        self.frames[self.frames_index] = f
        self.frames_index += 1
    
    def pop_frame(self) -> Frame:
        self.frames_index -= 1
        return self.frames[self.frames_index]

    def execute_index_expression(self, left: Object, index: Object) -> VmError | None:
        if type(left) is ArrayObject and type(index) is IntegerObject:
            return self.execute_array_index(left, index)
        elif type(left) is HashObject:
            return self.execute_hash_index(left, index)
        else:
            return VmError(f'index operator not supported for {type(left)}')

    def execute_array_index(self, array: Object, index: Object) -> VmError | None:
        i = index.value
        max_index = len(array.elements) - 1
        if i < 0 or i > max_index:
            return self.push(NULL)

        return self.push(array.elements[i])
    
    def execute_hash_index(self, hash_map: Object, key: Object) -> VmError | None:
        return self.push(hash_map.pairs.get(key, NULL))

    def execute_binary_operation(self, op: Opcode) -> VmError | None:
        right = self.pop()
        left = self.pop()

        if type(left) is IntegerObject and type(right) is IntegerObject:
            return self.execute_binary_integer_operation(op, left, right)
        elif type(left) is StringObject and type(right) is StringObject:
            return self.execute_binary_string_operation(op, left, right)
        
        return VmError(f'unsupported types for binary operation: {left.type()}, {right.type()}')

    def execute_binary_integer_operation(self, op: Opcode, left: IntegerObject, right: IntegerObject) -> VmError | None:
        left_val = left.value
        right_val = right.value

        if op == Opcode.OpAdd:
            result = left_val + right_val
        elif op == Opcode.OpSub:
            result = left_val - right_val
        elif op == Opcode.OpMul:
            result = left_val * right_val
        elif op == Opcode.OpDiv:
            result = left_val // right_val
        else:
            return VmError(f'unknown integer operator: {op}')
        
        return self.push(IntegerObject(result))
    
    def execute_binary_string_operation(self, op: Opcode, left: StringObject, right: StringObject) -> VmError | None:
        left_val = left.value
        right_val = right.value

        if op == Opcode.OpAdd:
            result = left_val + right_val
        else:
            return VmError(f'unknown string operator: {op}')
        
        return self.push(StringObject(result))
    
    def execute_comparison(self, op: Opcode) -> VmError | None:
        right = self.pop()
        left = self.pop()

        if type(left) == IntegerObject and type(right) == IntegerObject:
            return self.execute_integer_comparison(op, left, right)

        if op == Opcode.OpEqual:
            return self.push(self.native_bool_to_boolean_object(left == right))
        elif op == Opcode.OpNotEqual:
            return self.push(self.native_bool_to_boolean_object(left != right))
        else:
            return VmError(f'unknown boolean comparison operator: {op}')
            
    def execute_integer_comparison(self, op: Opcode, left: IntegerObject, right: IntegerObject) -> VmError | None:
        left_val = left.value
        right_val = right.value

        if op == Opcode.OpEqual:
            return self.push(self.native_bool_to_boolean_object(left_val == right_val))
        elif op == Opcode.OpNotEqual:
            return self.push(self.native_bool_to_boolean_object(left_val != right_val))
        elif op == Opcode.OpGreaterThan:
            return self.push(self.native_bool_to_boolean_object(left_val >  right_val))
        else:
            return VmError(f'unknown integer comparison operator: {op}')
        
        return self.push(TRUE if result else FALSE)

    def native_bool_to_boolean_object(self, b: bool) -> BooleanObject:
        return TRUE if b else FALSE

    def execute_bang_operator(self) -> VmError | None:
        operand = self.pop()

        if operand == TRUE:
            return self.push(FALSE)
        elif operand == FALSE:
            return self.push(TRUE)
        elif operand == NULL:
            return self.push(TRUE)
        else:
            return self.push(FALSE)

    def execute_minus_operator(self) -> VmError | None:
        operand = self.pop()

        if type(operand) != IntegerObject:
            return VmError(f'unsupported type for negation: {operand.type()}')
        
        return self.push(IntegerObject(-operand.value))

    def call_function(self, num_args: int) -> VmError | None:
        fn = self.stack[self.sp-1-num_args] # Function is below all the args on the stack
        if type(fn) is not CompiledFunction:
            return VmError('calling non-function')
        
        if num_args != fn.num_parameters:
            return VmError(f'wrong number of arguments: want={fn.num_parameters}, got={num_args}')
        
        # self.sp points at the slot above the args, but base_pointer needs to point
        # to the first arg so that it can appropriately clean them up when the call
        # is finished
        frame = Frame(fn, base_pointer=self.sp-num_args)
        self.push_frame(frame)
        # "Allocate" room on stack for the local variables of the function
        # before where the function will use the stack for actually doing
        # its work
        self.sp = frame.base_pointer + fn.num_locals

    def build_array(self, start: int, end: int) -> ArrayObject:
        elements = [None] * (end - start)
        for i in range(start, end):
            elements[i - start] = self.stack[i]
        return ArrayObject(elements)

    def build_hash(self, start: int, end: int) -> HashObject:
        pairs = {}
        for i in range(start, end, 2):
            key = self.stack[i]
            value = self.stack[i + 1]
            pairs[key] = value
        return HashObject(pairs=pairs)

    def is_truthy(self, obj: Object) -> bool:
        if type(obj) == BooleanObject:
            return obj.value
        elif obj == NULL:
            return False
        else:
            return True

    def push(self, o: Object) -> VmError | None:
        if self.sp >= STACK_SIZE:
            return VmError('stack overflow')
        
        self.stack[self.sp] = o
        self.sp += 1
        return None
    
    def pop(self) -> Object:
        o = self.stack[self.sp - 1]
        self.sp -= 1
        return o

    def stack_top(self) -> Object | None:
        if self.sp == 0:
            return None

        return self.stack[self.sp - 1]
    
    # This should only be used for testing
    def last_popped_stack_elem(self) -> Object:
        return self.stack[self.sp]