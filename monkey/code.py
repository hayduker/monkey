from typing import TypeAlias, List, Tuple
from dataclasses import dataclass
from enum import Enum



class Opcode(Enum):
    OpConstant       = b'\x01'
    OpPop            = b'\x02'
    OpAdd            = b'\x03'
    OpSub            = b'\x04'
    OpMul            = b'\x05'
    OpDiv            = b'\x06'
    OpTrue           = b'\x07'
    OpFalse          = b'\x08'
    OpEqual          = b'\x09'
    OpNotEqual       = b'\x0A'
    OpGreaterThan    = b'\x0B'
    OpMinus          = b'\x0C'
    OpBang           = b'\x0D'
    OpJumpNotTruthy  = b'\x0E'
    OpJump           = b'\x0F'
    OpNull           = b'\x10'
    OpSetGlobal      = b'\x11'
    OpGetGlobal      = b'\x12'
    OpArray          = b'\x13'
    OpHash           = b'\x14'
    OpIndex          = b'\x15'
    OpCall           = b'\x16'
    OpReturnValue    = b'\x17'
    OpReturn         = b'\x18'
    OpSetLocal       = b'\x19'
    OpGetLocal       = b'\x1A'
    OpGetBuiltin     = b'\x1B'
    OpGetFree        = b'\x1C'
    OpClosure        = b'\x1D'
    OpCurrentClosure = b'\x1E'


@dataclass
class Definition:
    name:           str
    operand_widths: List[int]


definitions = {
    Opcode.OpConstant:       Definition(name='OpConstant',       operand_widths=[2]),
    Opcode.OpAdd:            Definition(name='OpAdd',            operand_widths=[]),
    Opcode.OpPop:            Definition(name='OpPop',            operand_widths=[]),
    Opcode.OpSub:            Definition(name='OpSub',            operand_widths=[]),
    Opcode.OpMul:            Definition(name='OpMul',            operand_widths=[]),
    Opcode.OpDiv:            Definition(name='OpDiv',            operand_widths=[]),
    Opcode.OpTrue:           Definition(name='OpTrue',           operand_widths=[]),
    Opcode.OpFalse:          Definition(name='OpFalse',          operand_widths=[]),
    Opcode.OpEqual:          Definition(name='OpEqual',          operand_widths=[]),
    Opcode.OpNotEqual:       Definition(name='OpNotEqual',       operand_widths=[]),
    Opcode.OpGreaterThan:    Definition(name='OpGreaterThan',    operand_widths=[]),
    Opcode.OpMinus:          Definition(name='OpMinus',          operand_widths=[]),
    Opcode.OpBang:           Definition(name='OpBang',           operand_widths=[]),
    Opcode.OpJumpNotTruthy:  Definition(name='OpJumpNotTruthy',  operand_widths=[2]),
    Opcode.OpJump:           Definition(name='OpJump',           operand_widths=[2]),
    Opcode.OpNull:           Definition(name='OpNull',           operand_widths=[]),
    Opcode.OpSetGlobal:      Definition(name='OpSetGlobal',      operand_widths=[2]),
    Opcode.OpGetGlobal:      Definition(name='OpGetGlobal',      operand_widths=[2]),
    Opcode.OpArray:          Definition(name='OpArray',          operand_widths=[2]),
    Opcode.OpHash:           Definition(name='OpHash',           operand_widths=[2]),
    Opcode.OpIndex:          Definition(name='OpIndex',          operand_widths=[]),
    Opcode.OpCall:           Definition(name='OpCall',           operand_widths=[1]),
    Opcode.OpReturnValue:    Definition(name='OpReturnValue',    operand_widths=[]),
    Opcode.OpReturn:         Definition(name='OpReturn',         operand_widths=[]),
    Opcode.OpSetLocal:       Definition(name='OpSetLocal',       operand_widths=[1]),
    Opcode.OpGetLocal:       Definition(name='OpGetLocal',       operand_widths=[1]),
    Opcode.OpGetBuiltin:     Definition(name='OpGetBuiltin',     operand_widths=[1]),
    Opcode.OpGetFree:        Definition(name='OpGetFree',        operand_widths=[1]),
    Opcode.OpClosure:        Definition(name='OpClosure',        operand_widths=[2, 1]),
    Opcode.OpCurrentClosure: Definition(name='OpCurrentClosure', operand_widths=[]),
}


def lookup(op: bytes) -> Definition:
    defn = definitions.get(Opcode(op), None)
    if defn is None:
        raise ValueError(f'opcode {op} undefined')
    
    return defn


def make(op: Opcode, *operands: int) -> bytes:
    defn = definitions.get(op, None)
    if defn is None:
        return b''
    
    instruction = op.value
    for i, o in enumerate(operands):
        width = defn.operand_widths[i]
        if width == 1:
            instruction += o.to_bytes(1, byteorder='big')
        elif width == 2:
            instruction += o.to_bytes(2, byteorder='big')

    return instruction


class Instructions(bytearray):
    def fmt_instructions(self, defn: Definition, operands: List[int]) -> str:
        operand_count = len(defn.operand_widths)
        if len(operands) != operand_count:
            return f'ERROR: operand len {len(operands)} does not match defn {operand_count}'
        
        if operand_count == 0:
            return defn.name
        
        if operand_count == 1:
            return f'{defn.name} {operands[0]}'

        if operand_count == 2:
            return f'{defn.name} {operands[0]} {operands[1]}'
        
        return f'ERROR: unhandled operand_count for {defn.name}'

    def __str__(self):
        i = 0
        string = ''
        while i < len(self):
            defn = lookup(self[i].to_bytes(1))
            operands, read = read_operands(defn, self[i+1:])
            string += f'{i:04} {self.fmt_instructions(defn, operands)}\n'
            i += 1 + read
        
        return string


def read_uint8(ins: Instructions) -> int:
    return int.from_bytes(ins)


def read_uint16(ins: Instructions) -> int:
    return int.from_bytes(ins, byteorder='big')


def read_operands(defn: Definition, ins: Instructions) -> Tuple[List[int], int]:
    operands = []
    offset = 0

    for i, width in enumerate(defn.operand_widths):
        if width == 1:
            operands.append(read_uint8(ins[offset:offset + width]))
        elif width == 2:
            operands.append(read_uint16(ins[offset:offset + width]))

        offset += width

    return operands, offset