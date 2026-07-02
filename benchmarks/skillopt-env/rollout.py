"""yishuship PM benchmark rollout for SkillOpt."""
from __future__ import annotations

import json
import os
from pathlib import Path

from skillopt.model import chat_target


def _build_prompt(item: dict, skill_content: str) -> tuple[str, str]:
    system = skill_content
    if item.get("expected_flow"):
        user = (
            f"## 用户请求\n\n{item['scenario']}\n\n"
            f"## 背景信息\n\n{item.get('context', '无额外上下文。')}\n\n"
            f"## 任务\n\n"
            "请判断这个请求应该触发 yishuship 的哪些流程能力。\n"
            "输出需要包含：Route、Required flow steps、Why、Completion gate。\n"
            "不要实现功能；只给流程判断和下一步交付路径。\n"
        )
    else:
        user = (
            f"## 产品场景\n\n{item['scenario']}\n\n"
            f"## 背景信息\n\n{item.get('context', '无额外上下文。')}\n\n"
            f"## 任务\n\n"
            f"请为这个场景完成 **{item['stage']}** 阶段的产出。\n"
            f"严格遵循 skill 文档中的模板格式和退出标准。\n"
        )
    return system, user


def _score(output: str, item: dict) -> tuple[int, float, dict]:
    """用 pm_scorer 评分，返回 (hard, soft)。

    hard: 是否通过合格线 (0/1)
    soft: 归一化得分 (0.0-1.0)
    """
    if item.get("expected_flow"):
        try:
            from skillopt.envs.yishuship.matt_flow_scorer import score_matt_flow
        except ImportError:
            try:
                from matt_flow_scorer import score_matt_flow
            except ImportError:
                return 0, 0.0, {"error": "matt_flow_scorer unavailable"}

        result = score_matt_flow(output, item)
        max_score = result.get("max", 0.0)
        soft = result["total"] / max_score if max_score else 0.0
        return int(result["passOrFail"]), soft, result

    try:
        from skillopt.envs.yishuship.pm_scorer import score_stage
    except ImportError:
        try:
            from pm_scorer import score_stage
        except ImportError:
            keywords = item.get("ground_truth_keywords", [])
            if not keywords:
                return 0, 0.0, {"error": "pm_scorer unavailable"}
            hits = sum(1 for kw in keywords if kw.lower() in output.lower())
            soft = hits / len(keywords)
            return int(soft >= 0.6), soft, {
                "fallback": "keyword_match",
                "hits": hits,
                "total_keywords": len(keywords),
            }

    stage = item.get("stage", "discover")
    stage_map = {
        "发现": "discover", "discover": "discover",
        "定义": "define", "define": "define",
        "设计": "design", "design": "design",
        "验证": "validate", "validate": "validate",
        "实现": "build", "build": "build",
        "发布": "release", "release": "release",
        "观察": "observe", "observe": "observe",
        "学习": "learn", "learn": "learn",
    }
    scorer_key = stage_map.get(stage, stage)

    try:
        result = score_stage(scorer_key, output)
        total = result["total"]
        max_score = result["max"]
        passed = result["passOrFail"]
        soft = total / max_score if max_score > 0 else 0.0
        return int(passed), soft, result
    except Exception as exc:
        return 0, 0.0, {"error": str(exc), "stage": scorer_key}


def _fail_reason(score_details: dict) -> str:
    if score_details.get("error"):
        return str(score_details["error"])
    total = score_details.get("total", 0)
    max_score = score_details.get("max", 0)
    threshold = score_details.get("pass_threshold", "")
    return f"pm_scorer total={total}/{max_score}, threshold={threshold}"


def _write_prediction_trace(
    *,
    out_root: str,
    item: dict,
    system: str,
    user: str,
    prediction: str,
) -> None:
    task_dir = Path(out_root, "predictions", str(item["id"]))
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "target_system_prompt.txt").write_text(system, encoding="utf-8")
    (task_dir / "target_user_prompt.txt").write_text(user, encoding="utf-8")
    conversation = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
        {"role": "assistant", "content": prediction},
    ]
    (task_dir / "conversation.json").write_text(
        json.dumps(conversation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _rollout_one(item: dict, skill_content: str,
                 *, out_root: str, max_completion_tokens: int) -> dict:
    system, user = _build_prompt(item, skill_content)
    prediction, _usage = chat_target(
        system=system,
        user=user,
        max_completion_tokens=max_completion_tokens,
    )
    hard, soft, score_details = _score(prediction, item)
    _write_prediction_trace(
        out_root=out_root,
        item=item,
        system=system,
        user=user,
        prediction=prediction,
    )
    return {
        "id": str(item["id"]),
        "hard": hard,
        "soft": soft,
        "predicted_answer": prediction,
        "predicted_output": prediction,
        "scenario": item.get("scenario", ""),
        "stage": item.get("stage", "discover"),
        "task_type": item.get("task_type", "discover"),
        "task_description": item.get("scenario", ""),
        "target_system_prompt": system,
        "target_user_prompt": user,
        "score_details": score_details,
        "fail_reason": "" if hard else _fail_reason(score_details),
        "n_turns": 1,
    }


def run_batch(*, items: list[dict], skill_content: str, out_root: str,
              workers: int = 4, max_completion_tokens: int = 4096) -> list[dict]:
    os.makedirs(out_root, exist_ok=True)
    results = [
        _rollout_one(item, skill_content,
                     out_root=out_root,
                     max_completion_tokens=max_completion_tokens)
        for item in items
    ]
    Path(out_root, "rollouts.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2)
    )
    return results
