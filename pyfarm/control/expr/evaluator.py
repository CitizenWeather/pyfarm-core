"""Safe evaluation of alert and interlock expressions.

Expressions look like:

    "temperature.current > 28"
    "humidity_rh.current < 0.80 AND stage == fruiting"
    "sensor.co2.flatline_minutes > 10"
    "temperature.current < target - tolerance"

These are walked as an AST over a small whitelist of nodes and operators --
no ``eval()``/``exec()`` is ever used. ``AND``/``OR`` are accepted as
case-insensitive aliases for Python's ``and``/``or`` since that's the casing
used in GrowSpec YAML.
"""

from __future__ import annotations

import ast
import io
import operator
import tokenize
from typing import Any

from pyfarm.control.exceptions import SpecValidationError

_COMPARE_OPS: dict[type, Any] = {
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

_BOOL_OPS: dict[type, Any] = {
    ast.And: lambda values: all(values),
    ast.Or: lambda values: any(values),
}

_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPS: dict[type, Any] = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
}

_BOOL_WORD_REPLACEMENTS = {"AND": "and", "OR": "or"}


class SafeExpressionEvaluator:
    """Evaluates GrowSpec alert/interlock expressions against a known namespace.

    No ``exec()``/``eval()``: expressions are parsed with :mod:`ast` and walked
    over a whitelist of node types and operators.
    """

    def validate(self, expression: str, available_vars: set[str]) -> None:
        """Parse ``expression`` and check it only uses whitelisted operators
        and names drawn from ``available_vars``.

        Raises :class:`SpecValidationError` for anything else. Intended to be
        called at spec-load time, before any sensor is polled.
        """
        tree = self._parse(expression)
        self._check_node(tree.body, expression, available_vars)

    def evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        """Parse and evaluate ``expression`` against ``context``.

        ``context`` may be a nested dict (``{"temperature": {"current": 24.2}}``)
        addressed via dotted attribute access (``temperature.current``).
        """
        tree = self._parse(expression)
        return self._eval_node(tree.body, expression, context)

    # -- internals ---------------------------------------------------------

    def _parse(self, expression: str) -> ast.Expression:
        try:
            normalised = self._normalise_bool_words(expression)
            return ast.parse(normalised, mode="eval")
        except (SyntaxError, tokenize.TokenError) as exc:
            raise SpecValidationError(
                f"Invalid expression {expression!r}: {exc}"
            ) from exc

    def _normalise_bool_words(self, expression: str) -> str:
        """Rewrite the ``AND``/``OR`` *tokens* (not substrings) to lowercase.

        Operates on the token stream so that occurrences inside string
        literals (e.g. ``state == "ON AND OFF"``) are left untouched.
        """
        tokens = tokenize.generate_tokens(io.StringIO(expression).readline)
        rewritten = [
            (tok.type, _BOOL_WORD_REPLACEMENTS.get(tok.string, tok.string))
            if tok.type == tokenize.NAME
            else (tok.type, tok.string)
            for tok in tokens
        ]
        return tokenize.untokenize(rewritten)

    def _dotted_name(self, node: ast.AST, expression: str) -> str:
        parts: list[str] = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        else:
            raise SpecValidationError(
                f"Invalid expression {expression!r}: unsupported reference"
            )
        return ".".join(reversed(parts))

    def _name_allowed(self, dotted: str, available_vars: set[str]) -> bool:
        if dotted in available_vars:
            return True
        for pattern in available_vars:
            if pattern.endswith(".*") and dotted.startswith(pattern[:-1]):
                return True
        return False

    # -- validation -----------------------------------------------------

    def _check_node(
        self, node: ast.AST, expression: str, available_vars: set[str]
    ) -> None:
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: chained comparisons "
                    "are not supported"
                )
            if type(node.ops[0]) not in _COMPARE_OPS:
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unsupported "
                    f"comparison operator {type(node.ops[0]).__name__}"
                )
            self._check_node(node.left, expression, available_vars)
            self._check_node(node.comparators[0], expression, available_vars)
        elif isinstance(node, ast.BoolOp):
            if type(node.op) not in _BOOL_OPS:
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unsupported "
                    f"boolean operator {type(node.op).__name__}"
                )
            for value in node.values:
                self._check_node(value, expression, available_vars)
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _BIN_OPS:
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unsupported "
                    f"arithmetic operator {type(node.op).__name__}"
                )
            self._check_node(node.left, expression, available_vars)
            self._check_node(node.right, expression, available_vars)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in _UNARY_OPS:
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unsupported "
                    f"unary operator {type(node.op).__name__}"
                )
            self._check_node(node.operand, expression, available_vars)
        elif isinstance(node, (ast.Attribute, ast.Name)):
            dotted = self._dotted_name(node, expression)
            if not self._name_allowed(dotted, available_vars):
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unknown variable "
                    f"{dotted!r}"
                )
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float, str, bool)):
                raise SpecValidationError(
                    f"Invalid expression {expression!r}: unsupported constant "
                    f"{node.value!r}"
                )
        else:
            raise SpecValidationError(
                f"Invalid expression {expression!r}: unsupported syntax "
                f"{type(node).__name__}"
            )

    # -- evaluation -------------------------------------------------------

    def _eval_node(
        self, node: ast.AST, expression: str, context: dict[str, Any]
    ) -> Any:
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, expression, context)
            right = self._eval_node(node.comparators[0], expression, context)
            return _COMPARE_OPS[type(node.ops[0])](left, right)
        if isinstance(node, ast.BoolOp):
            values = [
                self._eval_node(value, expression, context)
                for value in node.values
            ]
            return _BOOL_OPS[type(node.op)](values)
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, expression, context)
            right = self._eval_node(node.right, expression, context)
            return _BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, expression, context)
            return _UNARY_OPS[type(node.op)](operand)
        if isinstance(node, (ast.Attribute, ast.Name)):
            dotted = self._dotted_name(node, expression)
            return self._resolve(dotted, expression, context)
        if isinstance(node, ast.Constant):
            return node.value
        raise SpecValidationError(
            f"Invalid expression {expression!r}: unsupported syntax "
            f"{type(node).__name__}"
        )

    def _resolve(self, dotted: str, expression: str, context: dict[str, Any]) -> Any:
        parts = dotted.split(".")
        if len(parts) == 1:
            # A bare identifier with no binding (e.g. an enum literal like
            # `fruiting` in `stage == fruiting`) evaluates to its own name.
            return context.get(parts[0], parts[0])

        value: Any = context
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise SpecValidationError(
                    f"Cannot evaluate {expression!r}: no value for {dotted!r}"
                )
        return value
