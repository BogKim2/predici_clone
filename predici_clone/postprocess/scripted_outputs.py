from __future__ import annotations

import ast
import math
import operator
from typing import Any


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCTIONS = {
    "abs": abs,
    "log": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "min": min,
    "max": max,
}


def evaluate_expression(expression: str, variables: dict[str, Any]) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return float(_eval_script(expression, variables))
    return float(_eval_node(tree.body, variables))


def evaluate_scripted_outputs(expressions: dict[str, str], variables: dict[str, float]) -> dict[str, float]:
    outputs = dict(variables)
    for name, expression in expressions.items():
        outputs[name] = evaluate_expression(expression, outputs)
    return {name: outputs[name] for name in expressions}


def _eval_node(node: ast.AST, variables: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Unknown variable: {node.id}")
        return variables[node.id]
    if isinstance(node, ast.List):
        return [_eval_node(item, variables) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(item, variables) for item in node.elts)
    if isinstance(node, ast.Subscript):
        value = _eval_node(node.value, variables)
        index = _eval_node(node.slice, variables)
        return value[int(index)]
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINARY_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _BINARY_OPERATORS[op_type](_eval_node(node.left, variables), _eval_node(node.right, variables))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _UNARY_OPERATORS[op_type](_eval_node(node.operand, variables))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in _FUNCTIONS:
            function = _FUNCTIONS[node.func.id]
        elif node.func.id in variables and callable(variables[node.func.id]):
            function = variables[node.func.id]
        else:
            raise ValueError(f"Unsupported function: {node.func.id}")
        args = [_eval_node(arg, variables) for arg in node.args]
        return function(*args)
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def _eval_script(script: str, variables: dict[str, Any]) -> Any:
    tree = ast.parse(script, mode="exec")
    scope: dict[str, Any] = dict(variables)
    last_value: Any = None
    for statement in tree.body:
        last_value = _eval_statement(statement, scope)
    if "result" in scope:
        return scope["result"]
    if last_value is None:
        raise ValueError("Script must assign result or end with an expression")
    return last_value


def _eval_statement(statement: ast.stmt, scope: dict[str, Any]) -> Any:
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ValueError("Only simple variable assignment is supported")
        scope[statement.targets[0].id] = _eval_node(statement.value, scope)
        return None
    if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
        name = statement.target.id
        if name not in scope:
            raise ValueError(f"Unknown variable: {name}")
        op_type = type(statement.op)
        if op_type not in _BINARY_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        scope[name] = _BINARY_OPERATORS[op_type](scope[name], _eval_node(statement.value, scope))
        return None
    if isinstance(statement, ast.For):
        if not isinstance(statement.target, ast.Name):
            raise ValueError("Only simple loop variables are supported")
        for value in _eval_iterable(statement.iter, scope):
            scope[statement.target.id] = value
            for inner in statement.body:
                _eval_statement(inner, scope)
        return None
    if isinstance(statement, ast.Expr):
        return _eval_node(statement.value, scope)
    raise ValueError(f"Unsupported script statement: {type(statement).__name__}")


def _eval_iterable(node: ast.AST, scope: dict[str, Any]):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
        args = [int(_eval_node(arg, scope)) for arg in node.args]
        if len(args) not in {1, 2, 3}:
            raise ValueError("range expects 1 to 3 arguments")
        return range(*args)
    value = _eval_node(node, scope)
    if not isinstance(value, (list, tuple, range)):
        raise ValueError("Loop iterable must be a list, tuple, or range")
    return value
