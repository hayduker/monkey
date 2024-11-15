from monkey import myast as ast
from monkey import code
from monkey import builtins
from monkey.object import *
from monkey.symbol_table import Symbol, SymbolTable, GlobalScope, LocalScope, BuiltinScope

from dataclasses import dataclass

# TODO: Make current_instructions a property


class Bytecode:
    def __init__(self, instructions, constants):
        self.instructions = code.Instructions(instructions)
        self.constants = constants
    

class EmittedInstruction:
    def __init__(self, opcode: code.Opcode = None, position: int = None):
        self.opcode = opcode
        self.position = position


class CompilerError(Exception):
    pass


@dataclass
class CompilationScope:
    instructions: code.Instructions
    last_instruction: EmittedInstruction
    previous_instruction: EmittedInstruction


class Compiler:
    def __init__(self):
        self.constants = []
        self.symbol_table = SymbolTable()

        for i, b in enumerate(builtins.builtins):
            self.symbol_table.define_builtin(i, b.name)

        scope = CompilationScope(
            instructions=code.Instructions(),
            last_instruction=EmittedInstruction(),
            previous_instruction=EmittedInstruction()
        )
        self.scopes = [scope]
        self.scope_index = 0

    @property
    def current_scope(self) -> CompilationScope:
        return self.scopes[self.scope_index]

    def enter_scope(self) -> None:
        scope = CompilationScope(
            instructions=code.Instructions(),
            last_instruction=EmittedInstruction(),
            previous_instruction=EmittedInstruction()
        )
        self.scopes.append(scope)
        self.scope_index += 1
        self.symbol_table = SymbolTable(self.symbol_table)

    def leave_scope(self) -> code.Instructions:
        instructions = self.current_scope.instructions
        self.scopes = self.scopes[:-1] # TODO: Change to "del self.scopes[-1]"?
        self.scope_index -= 1
        self.symbol_table = self.symbol_table.outer
        return instructions

    def compile(self, node: ast.Node) -> CompilerError | None:
        if type(node) is ast.Program:
            for stmt in node.statements:
                if (err := self.compile(stmt)) is not None:
                    return err

        elif type(node) is ast.ExpressionStatement:
            if (err := self.compile(node.expression)) is not None:
                return err
            self.emit(code.Opcode.OpPop)

        elif type(node) is ast.InfixExpression:
            if node.operator == '<':
                if (err := self.compile(node.right)) is not None:
                    return err

                if (err := self.compile(node.left)) is not None:
                    return err
                
                self.emit(code.Opcode.OpGreaterThan)
                return

            if (err := self.compile(node.left)) is not None:
                return err
            
            if (err := self.compile(node.right)) is not None:
                return err

            if node.operator == '+':
                self.emit(code.Opcode.OpAdd)
            elif node.operator == '-':
                self.emit(code.Opcode.OpSub)
            elif node.operator == '*':
                self.emit(code.Opcode.OpMul)
            elif node.operator == '/':
                self.emit(code.Opcode.OpDiv)
            elif node.operator == '>':
                self.emit(code.Opcode.OpGreaterThan)
            elif node.operator == '==':
                self.emit(code.Opcode.OpEqual)
            elif node.operator == '!=':
                self.emit(code.Opcode.OpNotEqual)
            else:
                return CompilerError(f'Unknown operator {node.operator}')
        
        elif type(node) is ast.PrefixExpression:
            if (err := self.compile(node.right)) is not None:
                return err

            if node.operator == '-':
                self.emit(code.Opcode.OpMinus)
            elif node.operator == '!':
                self.emit(code.Opcode.OpBang)
            else:
                return CompilerError(f'Unknown operator {node.operator}')
            
        elif type(node) is ast.IntegerLiteral:
            integer = IntegerObject(node.value)
            self.emit(code.Opcode.OpConstant, self.add_constant(integer))
        
        elif type(node) is ast.Boolean:
            if node.value:
                self.emit(code.Opcode.OpTrue)
            else:
                self.emit(code.Opcode.OpFalse)

        elif type(node) is ast.StringLiteral:
            string = StringObject(node.value)
            self.emit(code.Opcode.OpConstant, self.add_constant(string))

        elif type(node) is ast.IfExpression:
            if (err := self.compile(node.condition)) is not None:
                return err
            
            # Emit with bogus value that we change below
            jump_not_truthy_pos = self.emit(code.Opcode.OpJumpNotTruthy, 9999)

            if (err := self.compile(node.consequence)) is not None:
                return err
            
            if self.last_instruction_is(code.Opcode.OpPop):
                self.remove_last_pop()
            
            # Emit with bogus value that we change below
            jump_pos = self.emit(code.Opcode.OpJump, 9999)

            after_consequence_pos = len(self.current_scope.instructions)
            self.change_operand(jump_not_truthy_pos, after_consequence_pos)

            if node.alternative is None:
                self.emit(code.Opcode.OpNull)
            else:
                if (err := self.compile(node.alternative)) is not None:
                    return err
                
                if self.last_instruction_is(code.Opcode.OpPop):
                    self.remove_last_pop()
            
            after_alternative_pos = len(self.current_scope.instructions)
            self.change_operand(jump_pos, after_alternative_pos)
            
        elif type(node) is ast.BlockStatement:
            for stmt in node.statements:
                if (err := self.compile(stmt)) is not None:
                    return err

        elif type(node) is ast.LetStatement:
            if (err := self.compile(node.value)) is not None:
                return err
            
            symbol = self.symbol_table.define(node.name.value)
            if symbol.scope == GlobalScope:
                self.emit(code.Opcode.OpSetGlobal, symbol.index)
            else:
                self.emit(code.Opcode.OpSetLocal, symbol.index)
        
        elif type(node) is ast.Identifier:
            symbol = self.symbol_table.resolve(node.value)
            if symbol is None:
                return CompilerError(f'Undefined variable: {node.value}')
    
            self.load_symbol(symbol)

        elif type(node) is ast.ArrayLiteral:
            for elem in node.elements:
                if (err := self.compile(elem)) is not None:
                    return err
            
            self.emit(code.Opcode.OpArray, len(node.elements))
        
        elif type(node) is ast.HashLiteral:
            keys = list(node.pairs.keys())
            keys.sort(key=lambda x: str(x))

            for k in keys:
                if (err := self.compile(k)) is not None:
                    return err

                v = node.pairs[k]
                if (err := self.compile(v)) is not None:
                    return err
            
            self.emit(code.Opcode.OpHash, 2*len(node.pairs))

        elif type(node) is ast.IndexExpression:
            if (err := self.compile(node.left)) is not None:
                return err
            
            if (err := self.compile(node.index)) is not None:
                return err
            
            self.emit(code.Opcode.OpIndex)
        
        elif type(node) is ast.FunctionLiteral:
            self.enter_scope()

            for param in node.parameters:
                self.symbol_table.define(param.value)

            if (err := self.compile(node.body)) is not None:
                return err
            
            if self.last_instruction_is(code.Opcode.OpPop):
                self.replace_last_pop_with_return()

            if not self.last_instruction_is(code.Opcode.OpReturnValue):
                self.emit(code.Opcode.OpReturn)

            num_locals = self.symbol_table.num_definitions
            instructions = self.leave_scope()

            compiled_fn = CompiledFunction(instructions, num_locals, len(node.parameters))
            self.emit(code.Opcode.OpConstant, self.add_constant(compiled_fn))

        elif type(node) is ast.ReturnStatement:
            if (err := self.compile(node.return_value)) is not None:
                return err
            
            self.emit(code.Opcode.OpReturnValue)
        
        elif type(node) is ast.CallExpression:
            if (err := self.compile(node.function)) is not None:
                return err
        
            for arg in node.arguments:
                if (err := self.compile(arg)) is not None:
                    return err
            
            self.emit(code.Opcode.OpCall, len(node.arguments))

    def load_symbol(self, sym: Symbol) -> None:
        if sym.scope == GlobalScope:
            self.emit(code.Opcode.OpGetGlobal, sym.index)
        elif sym.scope == LocalScope:
            self.emit(code.Opcode.OpGetLocal, sym.index)
        elif sym.scope == BuiltinScope:
            self.emit(code.Opcode.OpGetBuiltin, sym.index)

    def find_or_add_binding(self, name: str) -> int:
        if name in self.bindings:
            return self.bindings[name]
        
        self.bindings[name] = len(self.bindings)
        return self.bindings[name]
    
    def add_constant(self, obj: Object) -> int:
        self.constants.append(obj)
        return len(self.constants) - 1
    
    def emit(self, op: code.Opcode, *operands: int) -> int:
        ins = code.make(op, *operands)
        pos = self.add_instruction(ins)
        self.set_last_instruction(op, pos)
        return pos

    def set_last_instruction(self, op: code.Opcode, pos: int):
        previous = self.current_scope.last_instruction
        last = EmittedInstruction(op, pos)
        self.current_scope.previous_instruction = previous
        self.current_scope.last_instruction = last

    def last_instruction_is(self, op: code.Opcode) -> bool:
        if len(self.current_scope.instructions) == 0:
            return False

        return self.current_scope.last_instruction.opcode == op
    
    def remove_last_pop(self) -> None:
        self.current_scope.instructions = self.current_scope.instructions[:self.current_scope.last_instruction.position]
        self.current_scope.last_instruction = self.current_scope.previous_instruction
    
    def replace_instruction(self, pos: int, new_instruction: bytes) -> None:
        for i in range(len(new_instruction)):
            self.current_scope.instructions[pos + i] = new_instruction[i]

    def replace_last_pop_with_return(self) -> None:
        last_pos = self.current_scope.last_instruction.position
        self.replace_instruction(last_pos, code.make(code.Opcode.OpReturnValue))
        self.current_scope.last_instruction.opcode = code.Opcode.OpReturnValue

    def change_operand(self, op_pos: int, operand: int) -> None:
        op = code.Opcode(self.current_scope.instructions[op_pos].to_bytes(1))
        new_instruction = code.make(op, operand)
        self.replace_instruction(op_pos, new_instruction)
    
    def add_instruction(self, ins: bytes) -> int:
        idx = len(self.current_scope.instructions)
        self.current_scope.instructions += code.Instructions(ins)
        return idx
        
    def bytecode(self) -> Bytecode:
        return Bytecode(self.current_scope.instructions, self.constants)
    
