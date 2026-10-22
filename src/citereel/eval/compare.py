from __future__ import annotations

from dataclasses import dataclass, field

from citereel.eval.report import SuiteReport


@dataclass
class CaseDelta:
    case_id: str
    left_passed: bool
    right_passed: bool
    left_kinds: list[str] = field(default_factory=list)
    right_kinds: list[str] = field(default_factory=list)
    latency_delta_ms: float = 0.0


@dataclass
class ComparisonReport:
    left_name: str
    right_name: str
    left_passed: int
    right_passed: int
    total: int
    regressions: list[CaseDelta] = field(default_factory=list)
    improvements: list[CaseDelta] = field(default_factory=list)
    unchanged: list[CaseDelta] = field(default_factory=list)
    left_latency_ms: float = 0.0
    right_latency_ms: float = 0.0


def compare_suite_reports(left: SuiteReport, right: SuiteReport) -> ComparisonReport:
    left_map = {c.case_id: c for c in left.cases}
    right_map = {c.case_id: c for c in right.cases}
    ids = sorted(set(left_map) | set(right_map))
    regressions: list[CaseDelta] = []
    improvements: list[CaseDelta] = []
    unchanged: list[CaseDelta] = []
    for case_id in ids:
        a = left_map.get(case_id)
        b = right_map.get(case_id)
        if a is None or b is None:
            continue
        delta = CaseDelta(
            case_id=case_id,
            left_passed=a.passed,
            right_passed=b.passed,
            left_kinds=list(a.failure_kinds),
            right_kinds=list(b.failure_kinds),
            latency_delta_ms=round(b.latency_ms - a.latency_ms, 2),
        )
        if a.passed and not b.passed:
            regressions.append(delta)
        elif (not a.passed) and b.passed:
            improvements.append(delta)
        else:
            unchanged.append(delta)
    return ComparisonReport(
        left_name=left.config_name,
        right_name=right.config_name,
        left_passed=left.passed_count,
        right_passed=right.passed_count,
        total=max(left.total, right.total),
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        left_latency_ms=left.total_latency_ms,
        right_latency_ms=right.total_latency_ms,
    )


def format_comparison(cmp: ComparisonReport) -> str:
    left_pct = _pct(cmp.left_passed, cmp.total)
    right_pct = _pct(cmp.right_passed, cmp.total)
    lines = [
        f"compare  {cmp.left_name} → {cmp.right_name}",
        f"passed   {cmp.left_passed}/{cmp.total} ({left_pct}) → "
        f"{cmp.right_passed}/{cmp.total} ({right_pct})",
        f"latency  {cmp.left_latency_ms:.1f}ms → {cmp.right_latency_ms:.1f}ms",
    ]
    if cmp.regressions:
        lines.append("regressions:")
        for d in cmp.regressions:
            kinds = ",".join(d.right_kinds) or "?"
            lines.append(f"  - {d.case_id}  ({kinds})")
    if cmp.improvements:
        lines.append("improvements:")
        for d in cmp.improvements:
            lines.append(f"  + {d.case_id}")
    if not cmp.regressions and not cmp.improvements:
        lines.append("no pass/fail changes across cases")
    return "\n".join(lines)


def format_suite_report(report: SuiteReport) -> str:
    rate = _pct(report.passed_count, report.total)
    kind_counts: dict[str, int] = {}
    for case in report.cases:
        for kind in case.failure_kinds:
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
    lines = [
        f"eval  suite={report.suite_id}  config={report.config_name}",
        f"pass  {report.passed_count}/{report.total} ({rate})  "
        f"latency={report.total_latency_ms:.1f}ms",
        f"docs  {report.docs_fingerprint[:16]}…",
    ]
    if kind_counts:
        parts = [f"{k}={kind_counts[k]}" for k in sorted(kind_counts)]
        lines.append(f"kinds {' '.join(parts)}")
    for case in report.cases:
        mark = "ok" if case.passed else "FAIL"
        extra = ""
        if case.failure_kinds:
            extra = f"  [{','.join(case.failure_kinds)}]"
        lines.append(f"  {mark:4}  {case.case_id}  {case.latency_ms:.0f}ms{extra}")
        for fail in case.failures[:3]:
            lines.append(f"        - {fail}")
    return "\n".join(lines)


def _pct(passed: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{round(100.0 * passed / total)}%"
