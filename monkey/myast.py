from typing import Protocol, Callable, Dict, List, Any
from abc import abstractmethod
from dataclasses import dataclass, field

from monkey.tokens import Token, TokenType

##########################################
# Super classes, mostly for organization #
##########################################

@dataclass
class Node:
    token: Token

    def token_literal(self) -> str:
        return self.token.literal

class Statement(Node): pass
class Expression(Node): pass

################################################
# Special Program  node for the top of the AST #
################################################

# This should technically inherit from Node but it breaks things... Programs don't
# have a token anyways
@dataclass
class Program:
    statements: [Statement] = field(default_factory=list)

    def token_literal() -> str:
        if len(self.statements) > 0:
            return self.statements[0].token_literal()
        
        return ''
    
    def __repr__(self) -> str:
        return 'Program(' + ',\n        '.join([str(s) for s in self.statements]) + ')'


####################
# Expression nodes #
####################


@dataclass
class Identifier(Expression):
    token: Token
    value: str
    
    def __repr__(self) -> str:
        return f'Identifier({self.value})'

    def __hash__(self) -> str:
        return hash(self.value)


@dataclass
class IntegerLiteral(Expression):
    token: Token
    value: int = None
    
    def __repr__(self) -> str:
        return f'IntegerLiteral({self.value})'

    def __hash__(self) -> str:
        return self.value

@dataclass
class StringLiteral(Expression):
    token: Token
    value: str = None

    def __repr__(self) -> str:
        return f'StringLiteral("{self.value}")'

    def __hash__(self) -> str:
        return hash(self.value)

@dataclass
class Boolean(Expression):
    token: Token
    value: bool

    def __repr__(self) -> str:
        return f'Boolean({self.value})'    

    def __hash__(self) -> str:
        return hash(self.value)

@dataclass
class BlockStatement:
    token: Token
    statements: List[Statement] = field(default_factory=list)

    def __repr__(self) -> str:
        return 'BlockStatement(' + ',\n               '.join([str(s) for s in self.statements]) + ')'


@dataclass
class IfExpression(Expression):
    token: Token
    condition: Expression = None
    consequence: BlockStatement = None
    alternative: BlockStatement = None

    def __repr__(self) -> str:
        # string = ''.join(['if ', str(self.condition), ' ', str(self.consequence)])
        # if self.alternative is not None:
        #     string += ''.join([' else ', str(self.alternative)])

        string = f'IfExpression({self.condition}, {self.consequence}'
        if self.alternative is not None:
            string += f', {self.alternative})'
        return string


@dataclass
class FunctionLiteral(Expression):
    token: Token
    parameters: List[Identifier] = field(default_factory=list)
    body: BlockStatement = None
    name: str = None

    def __repr__(self) -> str:
        params_string = ', '.join([str(p) for p in self.parameters])
        string = f'{self.token.literal}'
        if self.name != '':
            string + f'[{self.name}]'
        string += f'({params_string}) {self.body}'


@dataclass
class CallExpression(Expression):
    token: Token
    function: Expression # can be FunctionLiteral or Identifier
    arguments: List[Expression] = field(default_factory=list)

    def __repr__(self) -> str:
        arguments_string = ', '.join([str(a) for a in self.arguments])
        return f'{self.function}({arguments_string})'


@dataclass
class ArrayLiteral(Expression):
    token: Token
    elements: List[Expression] = field(default_factory=list)

    def __repr__(self) -> str:
        elements_string = ', '.join([str(e) for e in self.elements])
        return f'ArrayLiteral({elements_string})'    

    def __hash__(self) -> str:
        return hash(str(self))

@dataclass
class HashLiteral(Expression):
    token: Token
    pairs: Dict[Expression, Expression] = field(default_factory=dict)

    def __repr__(self) -> str:
        pairs_string = ', '.join([f'{str(k)}:{str(v)}' for k,v in self.pairs.items()])
        return 'HashLiteral(' + pairs_string + ')'


@dataclass
class IndexExpression(Expression):
    token: Token
    left: Expression
    index: Expression = None

    def __repr__(self) -> str:
        return f'({self.left}[{self.index}])'

    def __hash__(self) -> str:
        return hash(str(self))

@dataclass
class PrefixExpression:
    token: Token
    operator: str
    right: Expression = None
    
    def __repr__(self) -> str:
        return f'PrefixExpression({self.operator}{self.right})'

    def __hash__(self) -> str:
        return hash(str(self))

@dataclass
class InfixExpression:
    token: Token
    left: Expression
    operator: str
    right: Expression = None
    
    def __repr__(self) -> str:
        return f'InfixExpression({self.left} {self.operator} {self.right})'

    def __hash__(self) -> str:
        return hash(str(self))

###################
# Statement nodes #
###################


@dataclass
class LetStatement(Statement):
    token: Token
    name: Identifier = None
    value: Expression = None

    def __repr__(self) -> str:
        string = f'{self.token_literal()} {self.name} = '
        if self.value is not None:
            string += str(self.value)
        return string + ';'


@dataclass
class ReturnStatement(Statement):
    token: Token
    return_value: Expression = None

    def __repr__(self) -> str:
        string = f'{self.token_literal()} '
        if self.return_value is not None:
            string += str(self.return_value)
        return string +';'


@dataclass
class ExpressionStatement(Statement):
    token: Token
    expression: Expression = None

    def __repr__(self) -> str:
        return f'ExpressionStatement({self.expression})' if self.expression is not None else ''


def modify(node: Node, modifier: Callable[[Node], Node]) -> Node:
    if type(node) is Program:
        for i, statement in enumerate(node.statements):
            node.statements[i] = modify(statement, modifier)
    elif type(node) is ExpressionStatement:
        node.expression = modify(node.expression, modifier)
    elif type(node) is InfixExpression:
        node.left = modify(node.left, modifier)
        node.right = modify(node.right, modifier)
    elif type(node) is PrefixExpression:
        node.right = modify(node.right, modifier)
    elif type(node) is IndexExpression:
        node.left = modify(node.left, modifier)
        node.index = modify(node.index, modifier)
    elif type(node) is IfExpression:
        node.condition = modify(node.condition, modifier)
        node.consequence = modify(node.consequence, modifier)
        if node.alternative is not None:
            node.alternative = modify(node.alternative, modifier)
    elif type(node) is BlockStatement:
        for i, stmt in enumerate(node.statements):
            node.statements[i] = modify(stmt, modifier)
    elif type(node) is ReturnStatement:
        node.return_value = modify(node.return_value, modifier)
    elif type(node) is LetStatement:
        node.value = modify(node.value, modifier)
    elif type(node) is FunctionLiteral:
        for i, param in enumerate(node.parameters):
            node.parameters[i] = modify(param, modifier)
        node.body = modify(node.body, modifier)
    elif type(node) is ArrayLiteral:
        for i, elem in enumerate(node.elements):
            node.elements[i] = modify(elem, modifier)
    elif type(node) is HashLiteral:
        new_pairs = {}
        for key, val in node.pairs.items():
            new_key = modify(key, modifier)
            new_val = modify(val, modifier)
            new_pairs[new_key] = new_val
        node.pairs = new_pairs

    return modifier(node)


def display(program: Program) -> None:
    def depthy_print(input: Any, depth: int = 0, last: bool = False) -> None:
        if depth == 0:
            print(str(input))
            return

        if last:
            print('    ' * (depth-1) + '└── ' + str(input))
        else:
            print('    ' * (depth-1) + '├── ' + str(input))

    def display_node(node: Program | Node, depth: int = 0, last: bool = False) -> None:
        if type(node) is Program:
            depthy_print('Program')
            for stmt in node.statements[:-1]:
                display_node(stmt, depth + 1)
            display_node(node.statements[-1], depth + 1, last=True)
        elif type(node) is ExpressionStatement:
            depthy_print('ExpressionStatement', depth, last)
            display_node(node.expression, depth + 1, last=True)
        elif type(node) is InfixExpression:
            depthy_print(f'InfixExpression[{node.operator}]', depth, last)
            display_node(node.left, depth + 1)
            display_node(node.right, depth + 1, last=True)
        elif type(node) is PrefixExpression:
            depthy_print(f'PrefixExpression({node.operator})', depth, last)
            display_node(node.right, depth + 1, last=True)
        elif type(node) is IndexExpression:
            depthy_print('IndexExpression', depth, last)
            display_node(node.left, depth + 1)
            display_node(node.index, depth + 1, last=True)
        elif type(node) is IfExpression:
            depthy_print('IfExpression', depth, last)
            display_node(node.condition, depth + 1)
            if node.alternative is not None:
                display_node(node.consequence, depth + 1)
                display_node(node.alternative, depth + 1, last=True)
            else:
                display_node(node.consequence, depth + 1, last=True)
        elif type(node) is BlockStatement:
            depthy_print('BlockStatement', depth, last)
            for stmt in node.statements[:-1]:
                display_node(stmt, depth + 1)
            display_node(node.statements[-1], depth + 1, last=True)
        elif type(node) is ReturnStatement:
            depthy_print('ReturnStatement', depth, last)
            display_node(node.return_value, depth + 1, last=True)
        elif type(node) is LetStatement:
            depthy_print(f'LetStatement({node.name.value})', depth, last)
            display_node(node.value, depth + 1)
        elif type(node) is FunctionLiteral:
            depthy_print('FunctionLiteral', depth, last)
            for param in node.parameters:
                display_node(param, depth + 1)
            display_node(node.body, depth + 1, last=True)
        elif type(node) is ArrayLiteral:
            depthy_print('ArrayLiteral', depth, last)
            for elem in node.elements:
                display_node(elem, depth + 1)
        elif type(node) is HashLiteral:
            depthy_print('HashLiteral', depth, last)
            for key, val in node.pairs.items():
                display_node(key, depth + 1)
                display_node(val, depth + 1)
        elif type(node) is Identifier:
            depthy_print(f'Identifier({node.value})', depth, last)
        elif type(node) is IntegerLiteral:
            depthy_print(f'IntegerLiteral({node.value})', depth, last)
        elif type(node) is StringLiteral:
            depthy_print(f'StringLiteral("{node.value}")', depth, last)
        elif type(node) is Boolean:
            depthy_print(f'Boolean({node.value})', depth, last)
        elif type(node) is CallExpression:
            depthy_print('CallExpression', depth, last)
            if len(node.arguments) == 0:
                display_node(node.function, depth + 1, last=True)
            else:
                display_node(node.function, depth + 1)
                for arg in node.arguments[:-1]:
                    display_node(arg, depth + 1)
                display_node(node.arguments[-1], depth + 1, last=True)


        # else:
        #     return f'Unhandled node: {node}'
        
    display_node(program)

