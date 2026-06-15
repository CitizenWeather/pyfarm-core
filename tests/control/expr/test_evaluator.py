import pytest

from pyfarm.control.expr.evaluator import SafeExpressionEvaluator
from pyfarm.control.spec.exceptions import SpecValidationError


@pytest.fixture
def evaluator() -> SafeExpressionEvaluator:
    return SafeExpressionEvaluator()


NAMESPACE = {
    "temperature.current",
    "humidity_rh.current",
    "stage",
    "target",
    "tolerance",
    "sensor.*",
    "fruiting",
}


class TestValidate:
    def test_simple_comparison(self, evaluator: SafeExpressionEvaluator) -> None:
        evaluator.validate("temperature.current > 28", NAMESPACE)

    def test_boolean_combination_and(self, evaluator: SafeExpressionEvaluator) -> None:
        evaluator.validate(
            "humidity_rh.current < 0.80 AND stage == fruiting", NAMESPACE
        )

    def test_boolean_combination_or(self, evaluator: SafeExpressionEvaluator) -> None:
        evaluator.validate(
            "temperature.current > 28 OR temperature.current < 0", NAMESPACE
        )

    def test_dotted_wildcard_name(self, evaluator: SafeExpressionEvaluator) -> None:
        evaluator.validate("sensor.co2.flatline_minutes > 10", NAMESPACE)

    def test_arithmetic_in_comparison(self, evaluator: SafeExpressionEvaluator) -> None:
        evaluator.validate("temperature.current < target - tolerance", NAMESPACE)

    def test_unknown_variable_rejected(self, evaluator: SafeExpressionEvaluator) -> None:
        with pytest.raises(SpecValidationError, match="unknown variable"):
            evaluator.validate("pressure.current > 28", NAMESPACE)

    def test_function_call_rejected(self, evaluator: SafeExpressionEvaluator) -> None:
        with pytest.raises(SpecValidationError):
            evaluator.validate("__import__('os').system('ls')", NAMESPACE)

    def test_list_literal_rejected(self, evaluator: SafeExpressionEvaluator) -> None:
        with pytest.raises(SpecValidationError):
            evaluator.validate("temperature.current in [1, 2, 3]", NAMESPACE)

    def test_invalid_syntax_rejected(self, evaluator: SafeExpressionEvaluator) -> None:
        with pytest.raises(SpecValidationError, match="Invalid expression"):
            evaluator.validate("temperature.current >", NAMESPACE)


class TestEvaluate:
    def test_simple_comparison_true(self, evaluator: SafeExpressionEvaluator) -> None:
        context = {"temperature": {"current": 30}}
        assert evaluator.evaluate("temperature.current > 28", context) is True

    def test_simple_comparison_false(self, evaluator: SafeExpressionEvaluator) -> None:
        context = {"temperature": {"current": 20}}
        assert evaluator.evaluate("temperature.current > 28", context) is False

    def test_boolean_and(self, evaluator: SafeExpressionEvaluator) -> None:
        context = {"humidity_rh": {"current": 0.5}, "stage": "fruiting"}
        assert (
            evaluator.evaluate(
                "humidity_rh.current < 0.80 AND stage == fruiting", context
            )
            is True
        )

    def test_enum_literal_comparison(self, evaluator: SafeExpressionEvaluator) -> None:
        context = {"stage": "initiation"}
        assert (
            evaluator.evaluate("stage == fruiting", context) is False
        )

    def test_arithmetic_with_named_values(
        self, evaluator: SafeExpressionEvaluator
    ) -> None:
        context = {"temperature": {"current": 15}, "target": 18, "tolerance": 2}
        assert (
            evaluator.evaluate("temperature.current < target - tolerance", context)
            is True
        )
