"""Deterministic scorer for Matt Pocock flow routing in yishuship.

This scorer checks whether a target skill reliably triggers the expected
workflow disciplines: alignment, PRD/test seams, vertical slices, TDD,
two-axis review, and handoff.
"""
from __future__ import annotations

import re


FLOW_DEFINITIONS: dict[str, dict[str, object]] = {
    "alignment": {
        "label": "alignment / grilling before building",
        "patterns": [
            r"\balignment\b",
            r"\bgrill(?:ing|-with-docs|-me)?\b",
            r"对齐|澄清|追问|访谈",
            r"shared language|CONTEXT\.md|domain model|领域模型|术语",
        ],
    },
    "shared_language": {
        "label": "shared language and durable project memory",
        "patterns": [
            r"shared language|CONTEXT\.md|domain model",
            r"共享语言|统一术语|领域模型|术语表",
            r"docs/decisions|ADR|DEC-\d+|决策记录",
        ],
    },
    "prd_test_seams": {
        "label": "PRD with acceptance criteria and test seams",
        "patterns": [
            r"\bPRD\b",
            r"test seams?|测试\s*seams?|测试边界|测试接口",
            r"acceptance|验收|Given.*When.*Then",
            r"规格|spec",
        ],
    },
    "vertical_slices": {
        "label": "vertical slices / tracer bullets",
        "patterns": [
            r"vertical slices?|tracer bullets?",
            r"垂直切片|端到端切片|纵向切片",
            r"independent(?:ly)?\s+(?:demo|verify|ship)",
            r"可独立.*(?:演示|验证|交付)",
        ],
    },
    "tdd": {
        "label": "TDD red-green-refactor loop",
        "patterns": [
            r"\bTDD\b",
            r"red[- ]green|red before green|red-green-refactor",
            r"failing test|失败测试|先写.*测试",
            r"红绿|红-绿|回归测试",
        ],
    },
    "two_axis_review": {
        "label": "two-axis code review: Standards and Spec",
        "patterns": [
            r"two[- ]axis|双轴",
            r"Standards?.*Spec|Spec.*Standards?",
            r"标准轴.*规格轴|规格轴.*标准轴",
            r"code-review|代码审查|对照.*PRD",
        ],
    },
    "handoff": {
        "label": "handoff with durable artifacts",
        "patterns": [
            r"\bhandoff\b",
            r"交接|上下文交接|移交",
            r"PR|CI|release|发布",
            r"artifact|产物|证据|路径",
        ],
    },
    "prototype": {
        "label": "throwaway prototype for unresolved design questions",
        "patterns": [
            r"\bprototype\b|runnable answer|throwaway",
            r"原型|可运行.*答案|一次性|临时 demo",
            r"用原型|先做.*demo|验证.*交互",
        ],
    },
    "diagnosis": {
        "label": "diagnosing-bugs tight feedback loop",
        "patterns": [
            r"diagnosing-bugs|tight feedback",
            r"reproduce|minimi[sz]e|hypothes|instrument|regression",
            r"复现|最小化|假设|插桩|定位|回归测试",
        ],
    },
    "deep_module": {
        "label": "codebase-design deep module vocabulary",
        "patterns": [
            r"deep modules?|codebase-design",
            r"module.*interface.*depth|interface.*implementation",
            r"seam|adapter|leverage|locality",
            r"模块.*接口|深模块|适配器|边界|局部性",
        ],
    },
}


FORBIDDEN_DEFINITIONS: dict[str, dict[str, object]] = {
    "skip_alignment": {
        "label": "skips alignment/PRD for an ambiguous product request",
        "patterns": [
            r"无需.*(?:对齐|澄清|PRD|规格)",
            r"跳过.*(?:对齐|澄清|PRD|规格)",
            r"直接(?:开始)?(?:实现|写代码).*(?:无需|不用)",
        ],
    },
}


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        for pattern in patterns
    )


def _score_named_checks(
    *,
    text: str,
    names: list[str],
    definitions: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    details: dict[str, dict[str, object]] = {}
    for name in names:
        definition = definitions.get(name)
        if not definition:
            details[name] = {
                "label": "unknown check",
                "hit": False,
                "unknown": True,
            }
            continue
        patterns = [str(pattern) for pattern in definition["patterns"]]
        details[name] = {
            "label": definition["label"],
            "hit": _has_any(text, patterns),
        }
    return details


def score_matt_flow(output: str, item: dict) -> dict:
    expected = item.get("expected_flow") or {}
    required = [str(name) for name in expected.get("required", [])]
    forbidden = [str(name) for name in expected.get("forbidden", [])]

    if not required:
        return {
            "total": 0.0,
            "max": 0.0,
            "pass_threshold": 0.0,
            "passOrFail": False,
            "details": {},
            "error": "expected_flow.required is empty",
        }

    required_details = _score_named_checks(
        text=output,
        names=required,
        definitions=FLOW_DEFINITIONS,
    )
    forbidden_details = _score_named_checks(
        text=output,
        names=forbidden,
        definitions=FORBIDDEN_DEFINITIONS,
    )

    required_hits = sum(1 for detail in required_details.values() if detail["hit"])
    forbidden_hits = sum(1 for detail in forbidden_details.values() if detail["hit"])
    total = max(0, required_hits - forbidden_hits)
    passed = required_hits == len(required) and forbidden_hits == 0

    return {
        "total": float(total),
        "max": float(len(required)),
        "pass_threshold": float(len(required)),
        "passOrFail": passed,
        "details": {
            "required": required_details,
            "forbidden": forbidden_details,
            "required_hits": required_hits,
            "forbidden_hits": forbidden_hits,
        },
    }
