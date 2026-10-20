"""Fixed-suite evaluation: verify, compare, and reproduce RAG run quality."""

from citereel.eval.compare import compare_suite_reports, format_comparison
from citereel.eval.dataset import EvalCase, EvalSuite, load_suite
from citereel.eval.report import CaseResult, SuiteReport
from citereel.eval.runner import RagConfig, run_suite

__all__ = [
    "CaseResult",
    "EvalCase",
    "EvalSuite",
    "RagConfig",
    "SuiteReport",
    "compare_suite_reports",
    "format_comparison",
    "load_suite",
    "run_suite",
]
