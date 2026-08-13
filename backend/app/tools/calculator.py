from __future__ import annotations

import ast
import math
import operator
import time
from typing import Any, Callable

from app.tools.base import BaseTool
from app.tools.schemas import (
    ToolExecutionResult,
    ToolMetadata,
)


BinaryOperator = Callable[
    [float | int, float | int],
    float | int,
]

UnaryOperator = Callable[
    [float | int],
    float | int,
]


class CalculatorTool(BaseTool):
    """
    Safely evaluate basic mathematical expressions.

    Supported operations:

    - Addition
    - Subtraction
    - Multiplication
    - Division
    - Floor division
    - Modulo
    - Power
    - Parentheses
    - Unary plus and minus

    Python eval is intentionally not used.
    """

    MAX_EXPRESSION_LENGTH = 500
    MAX_POWER_EXPONENT = 100
    MAX_ABSOLUTE_RESULT = 1e100

    BINARY_OPERATORS: dict[
        type[ast.operator],
        BinaryOperator,
    ] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    UNARY_OPERATORS: dict[
        type[ast.unaryop],
        UnaryOperator,
    ] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            description=(
                "Safely evaluates basic mathematical expressions "
                "without executing arbitrary Python code."
            ),
            version="1.0.0",
            requires_approval=False,
        )

    async def execute(
        self,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = time.perf_counter()

        try:
            expression = self._extract_expression(
                arguments,
            )

            parsed_expression = ast.parse(
                expression,
                mode="eval",
            )

            result = self._evaluate_node(
                parsed_expression.body,
            )

            result = self._validate_result(
                result,
            )

            execution_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=round(
                    execution_time_ms,
                    2,
                ),
                metadata={
                    "expression": expression,
                },
            )

        except Exception as exception:
            execution_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=self._format_error(
                    exception,
                ),
                execution_time_ms=round(
                    execution_time_ms,
                    2,
                ),
                metadata={},
            )

    def _extract_expression(
        self,
        arguments: dict[str, Any],
    ) -> str:
        expression_value = arguments.get(
            "expression",
        )

        if expression_value is None:
            raise ValueError(
                "Calculator requires an 'expression' argument."
            )

        expression = str(
            expression_value,
        ).strip()

        if not expression:
            raise ValueError(
                "Calculator expression cannot be empty."
            )

        if (
            len(expression)
            > self.MAX_EXPRESSION_LENGTH
        ):
            raise ValueError(
                "Calculator expression is too long."
            )

        return expression

    def _evaluate_node(
        self,
        node: ast.AST,
    ) -> float | int:
        if isinstance(
            node,
            ast.Constant,
        ):
            return self._evaluate_constant(
                node,
            )

        if isinstance(
            node,
            ast.BinOp,
        ):
            return self._evaluate_binary_operation(
                node,
            )

        if isinstance(
            node,
            ast.UnaryOp,
        ):
            return self._evaluate_unary_operation(
                node,
            )

        raise ValueError(
            "The expression contains an unsupported operation."
        )

    def _evaluate_constant(
        self,
        node: ast.Constant,
    ) -> float | int:
        value = node.value

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "Boolean values are not supported."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise ValueError(
                "Only numeric values are supported."
            )

        return value

    def _evaluate_binary_operation(
        self,
        node: ast.BinOp,
    ) -> float | int:
        operator_function = self.BINARY_OPERATORS.get(
            type(node.op),
        )

        if operator_function is None:
            raise ValueError(
                "The binary operation is not supported."
            )

        left_value = self._evaluate_node(
            node.left,
        )

        right_value = self._evaluate_node(
            node.right,
        )

        if isinstance(
            node.op,
            ast.Pow,
        ):
            if abs(right_value) > self.MAX_POWER_EXPONENT:
                raise ValueError(
                    "The exponent is too large."
                )

        result = operator_function(
            left_value,
            right_value,
        )

        return self._validate_result(
            result,
        )

    def _evaluate_unary_operation(
        self,
        node: ast.UnaryOp,
    ) -> float | int:
        operator_function = self.UNARY_OPERATORS.get(
            type(node.op),
        )

        if operator_function is None:
            raise ValueError(
                "The unary operation is not supported."
            )

        operand_value = self._evaluate_node(
            node.operand,
        )

        result = operator_function(
            operand_value,
        )

        return self._validate_result(
            result,
        )

    def _validate_result(
        self,
        value: float | int,
    ) -> float | int:
        if isinstance(
            value,
            float,
        ):
            if not math.isfinite(
                value,
            ):
                raise ValueError(
                    "The calculation produced a non-finite result."
                )

        if abs(value) > self.MAX_ABSOLUTE_RESULT:
            raise ValueError(
                "The calculation result is too large."
            )

        return value

    @staticmethod
    def _format_error(
        exception: Exception,
    ) -> str:
        if isinstance(
            exception,
            ZeroDivisionError,
        ):
            return "Division by zero is not allowed."

        if isinstance(
            exception,
            SyntaxError,
        ):
            return "The mathematical expression is invalid."

        exception_message = str(
            exception,
        ).strip()

        if exception_message:
            return exception_message[:1000]

        return type(exception).__name__