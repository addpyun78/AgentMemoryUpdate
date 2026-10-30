#!/usr/bin/env python3
"""Bind maintained role-learning profiles to executable A2A tasks."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "role-learning-registry.json"
SKILLS_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PROFILE_COUNT = 14
MARKER = "[A2A_LEARNING_PROFILES]"
SKILL_LOAD_MARKER = "[A2A_NATIVE_SKILL_LOAD]"
SELF_IMPROVEMENT_MARKER = "[A2A_SELF_IMPROVEMENT]"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema") != "a2a-role-learning-registry/v1":
        raise ValueError("invalid role learning registry schema")
    profiles = registry.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != REQUIRED_PROFILE_COUNT:
        raise ValueError(f"role learning registry must contain {REQUIRED_PROFILE_COUNT} profiles")
    ids = [str(profile.get("id") or "") for profile in profiles if isinstance(profile, dict)]
    if "" in ids or len(ids) != len(set(ids)):
        raise ValueError("role learning profile ids must be non-empty and unique")
    required_skills = sorted({
        str(skill).strip()
        for profile in profiles
        if isinstance(profile, dict)
        for skill in profile.get("required_local_skills") or []
        if str(skill).strip()
    })
    missing_assets = [
        skill for skill in required_skills
        if not (SKILLS_ROOT / skill / "SKILL.md").is_file()
    ]
    if missing_assets:
        raise ValueError(
            "role learning registry references missing native Hermes skills: "
            + ", ".join(missing_assets)
        )
    return registry


def _matches(profile: dict[str, Any], task: dict[str, Any]) -> bool:
    team = str(task.get("team") or "").upper()
    role = str(task.get("role_marker") or "").upper()
    team_patterns = [str(value).upper() for value in profile.get("team_patterns") or []]
    role_patterns = [str(value).upper() for value in profile.get("role_patterns") or []]
    return any(pattern == team for pattern in team_patterns) or any(pattern in role for pattern in role_patterns)


def _dedupe(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = _canonical(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def profiles_for_task(task: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = [profile for profile in registry["profiles"] if _matches(profile, task)]
    if not profiles:
        profiles = [profile for profile in registry["profiles"] if profile["id"] == "production-project-management"]
    return profiles


def _contract(
    task: dict[str, Any],
    profiles: list[dict[str, Any]],
    registry_hash: str,
    registry_version: str,
) -> dict[str, Any]:
    return {
        "schema": "a2a-role-learning-contract/v1",
        "registry_version": registry_version,
        "registry_sha256": registry_hash,
        "profile_ids": [profile["id"] for profile in profiles],
        "profile_names_ko": [profile["name_ko"] for profile in profiles],
        "knowledge": _dedupe([
            {"profile_id": profile["id"], "statement": statement}
            for profile in profiles
            for statement in profile.get("knowledge") or []
        ]),
        "required_local_skills": _dedupe([
            skill for profile in profiles for skill in profile.get("required_local_skills") or []
        ]),
        "upstream_capability_sources": _dedupe([
            skill for profile in profiles for skill in profile.get("upstream_capability_sources") or []
        ]),
        "required_capabilities": _dedupe([
            capability for profile in profiles for capability in profile.get("required_capabilities") or []
        ]),
        "expected_artifacts": _dedupe([
            artifact for profile in profiles for artifact in profile.get("expected_artifacts") or []
        ]),
        "gpu_policies": _dedupe([profile.get("gpu_policy") for profile in profiles]),
        "evidence_rules": _dedupe([profile.get("evidence_rule") for profile in profiles]),
        "native_learning": {
            "backend": "hermes-skills",
            "loader_tool": "skill_view",
            "load_before_task_actions": True,
            "required_skill_names": _dedupe([
                skill for profile in profiles for skill in profile.get("required_local_skills") or []
            ]),
            "memory_boundary": (
                "Reusable procedures belong in native Hermes skills. Durable user and environment facts belong "
                "in memory. Task progress, outputs, and temporary checklist state stay conversation-scoped."
            ),
            "failure_recovery": (
                "If a required skill cannot be loaded, keep passed work, use the embedded role knowledge for the "
                "bounded task, record the missing skill, repair the skill route, and retry only that task."
            ),
            "continuous_improvement": {
                "capture_tool": "skill_manage",
                "eligible_when": (
                    "The method was proven in the current task, is reusable across projects, is not already "
                    "covered by a loaded skill, and is not temporary task state."
                ),
                "candidate_lifecycle": (
                    "Create or patch an agent-created candidate skill so native Hermes usage telemetry and "
                    "Curator can maintain it. Promote it into the installer-controlled company skill root only "
                    "after repeated successful use and independent validation."
                ),
                "result_values": ["none", "created", "patched"],
            },
        },
        "application_rule": (
            "Before task actions, load every required local skill with native Hermes skill_view. Apply the bound "
            "knowledge and loaded skills to the task's normal owned artifacts. Record applied profile ids, actual "
            "skill loads, inspected evidence, and bounded repair in the task result."
        ),
    }


def _instruction(base: str, contract: dict[str, Any]) -> str:
    clean = str(base or "").split(f"\n{MARKER}", 1)[0].rstrip()
    knowledge = " | ".join(row["statement"] for row in contract["knowledge"])
    return (
        f"{clean}\n{MARKER} {', '.join(contract['profile_ids'])}\n"
        f"[A2A_REQUIRED_LOCAL_SKILLS] {', '.join(contract['required_local_skills'])}\n"
        f"{SKILL_LOAD_MARKER} Before any task action, call native Hermes "
        f"skill_view(name) once for each of: {', '.join(contract['required_local_skills'])}.\n"
        f"{SELF_IMPROVEMENT_MARKER} After verified work, use native skill_manage only for a proven, "
        "non-duplicate procedure reusable across projects; never save task progress or temporary outputs as a skill.\n"
        f"[A2A_ROLE_KNOWLEDGE] {knowledge}\n"
        f"[A2A_EXPECTED_LEARNING_ARTIFACTS] {', '.join(contract['expected_artifacts'])}\n"
        "Apply these rules to the assigned work and return [A2A_SKILL_USAGE] JSON containing loaded_skills, "
        "applied_profile_ids, affected_artifacts, evidence_paths, and improvement_action (none|created|patched) "
        "with its reason and skill_name when applicable; do not merely repeat profile names. "
        "If a skill load fails, record it, continue the bounded task from embedded knowledge, repair that route, "
        "and retry only the affected task. Preserve passed units and repair only failed scope."
    )


def bind_tasks(tasks: list[dict[str, Any]], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_registry()
    registry_hash = _digest(registry)
    bindings: dict[str, Any] = {}
    coverage: dict[str, int] = {profile["id"]: 0 for profile in registry["profiles"]}
    for task in tasks:
        profiles = profiles_for_task(task, registry)
        contract = _contract(task, profiles, registry_hash, str(registry["version"]))
        task["learning_contract"] = contract
        task["dispatch_instruction"] = _instruction(task.get("dispatch_instruction", ""), contract)
        task_id = str(task.get("task_id") or "")
        bindings[task_id] = {
            "role_marker": task.get("role_marker"),
            "team": task.get("team"),
            "profile_ids": contract["profile_ids"],
            "contract_sha256": _digest(contract),
        }
        for profile_id in contract["profile_ids"]:
            coverage[profile_id] += 1
    return {
        "schema": "a2a-role-learning-plan/v1",
        "registry_version": registry["version"],
        "registry_sha256": registry_hash,
        "source_report": registry.get("source_report"),
        # Keep the generated A2A_ROLE_LEARNING.json self-contained so a
        # reinstalled machine does not depend on the original research drive.
        "profile_catalog": registry["profiles"],
        "profile_task_coverage": coverage,
        "task_bindings": bindings,
    }


def validate_bound_tasks(tasks: list[dict[str, Any]], role_learning: dict[str, Any], registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry or load_registry()
    issues: list[str] = []
    valid_ids = {profile["id"] for profile in registry["profiles"]}
    expected_hash = _digest(registry)
    if role_learning.get("registry_sha256") != expected_hash:
        issues.append("role learning registry hash mismatch")
    if len(role_learning.get("profile_catalog") or []) != REQUIRED_PROFILE_COUNT:
        issues.append("role learning profile catalog is incomplete")
    bindings = role_learning.get("task_bindings") or {}
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        contract = task.get("learning_contract")
        if not isinstance(contract, dict):
            issues.append(f"{task_id} has no learning contract")
            continue
        profile_ids = contract.get("profile_ids") or []
        if not profile_ids or not set(profile_ids).issubset(valid_ids):
            issues.append(f"{task_id} has invalid learning profile ids")
        for field in ("knowledge", "required_local_skills", "required_capabilities", "expected_artifacts", "evidence_rules"):
            if not contract.get(field):
                issues.append(f"{task_id} learning contract missing {field}")
        instruction = str(task.get("dispatch_instruction") or "")
        if (
            MARKER not in instruction
            or "[A2A_REQUIRED_LOCAL_SKILLS]" not in instruction
            or SKILL_LOAD_MARKER not in instruction
            or SELF_IMPROVEMENT_MARKER not in instruction
            or "skill_view(name)" not in instruction
            or "skill_manage" not in instruction
            or "[A2A_SKILL_USAGE]" not in instruction
        ):
            issues.append(f"{task_id} dispatch does not carry learning markers")
        native_learning = contract.get("native_learning")
        if not isinstance(native_learning, dict):
            issues.append(f"{task_id} learning contract missing native Hermes backend")
        else:
            if native_learning.get("backend") != "hermes-skills":
                issues.append(f"{task_id} learning contract uses a non-native backend")
            if native_learning.get("required_skill_names") != contract.get("required_local_skills"):
                issues.append(f"{task_id} native skill load list mismatch")
            improvement = native_learning.get("continuous_improvement")
            if not isinstance(improvement, dict) or improvement.get("capture_tool") != "skill_manage":
                issues.append(f"{task_id} learning contract missing native self-improvement")
        binding = bindings.get(task_id)
        if not isinstance(binding, dict) or binding.get("contract_sha256") != _digest(contract):
            issues.append(f"{task_id} role learning binding mismatch")
    return issues


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(json.dumps({"status": "repair_required", "issues": ["Pass A2A_AGENT_TEAM.json"]}))
        return 0
    plan_path = Path(argv[1])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    tasks = [row for row in plan.get("tasks") or [] if isinstance(row, dict)]
    role_learning = bind_tasks(tasks)
    plan["tasks"] = tasks
    plan["role_learning"] = role_learning
    issues = validate_bound_tasks(tasks, role_learning)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    output_path = plan_path.with_name("A2A_ROLE_LEARNING.json")
    output_path.write_text(json.dumps(role_learning, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "repair_required" if issues else "ready",
        "tasks": len(tasks),
        "profiles": len(role_learning["profile_catalog"]),
        "output_path": str(output_path),
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

