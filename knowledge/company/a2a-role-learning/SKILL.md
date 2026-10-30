---
name: a2a-role-learning
description: Binds verified role knowledge to A2A worker tasks.
license: MIT
metadata:
  hermes:
    category: automation
    tags: [a2a, roles, learning, orchestration, evidence]
    related_skills: [a2a-automation-system, a2a-core-runtime]
---

# A2A Role Learning Skill

This is a native Hermes skill loaded through `skills.external_dirs`. It turns the approved 14-team learning report into executable worker contracts without introducing a second memory or learning engine. It does not fine-tune a model or replace project-specific research; it binds maintained knowledge, native local skills, expected artifacts, and evidence rules to every generated A2A task.

## When to Use

- When `A2A_AGENT_TEAM.json` is generated or regenerated.
- When a worker role, team, or orchestration lead is added.
- When approved company knowledge must reach real workers rather than remain in a report.
- When auditing whether each task received the correct learning profile.

## Prerequisites

- The A2A automation system and its team planner must be present.
- Hermes must expose this skill root through `skills.external_dirs`; confirm with `hermes skills list`.
- Read `references/role-learning-registry.json` when changing team knowledge or role routing.
- Use only bundled local skill identifiers listed by the registry. Upstream skill names are provenance notes, not runtime dependencies.

## How to Run

The automation planner loads `scripts/compile_role_learning.py` automatically. For an isolated audit, run:

```text
python scripts/compile_role_learning.py <A2A_AGENT_TEAM.json>
```

The normal planner writes `A2A_ROLE_LEARNING.json` beside `A2A_AGENT_TEAM.json`.

## Quick Reference

- Registry: `references/role-learning-registry.json`
- Compiler and validator: `scripts/compile_role_learning.py`
- Runtime marker: `[A2A_LEARNING_PROFILES]`
- Task field: `learning_contract`
- Plan field: `role_learning`
- Native backend: Hermes `skill_view` and the configured external skill root
- Memory boundary: durable facts in memory; reusable procedures in skills; task progress in the conversation

## Procedure

1. Match each task by its exact `team` and base `role_marker`.
2. Combine all applicable profiles without duplicating knowledge, skills, capabilities, or artifacts.
3. Resolve every `required_local_skills` entry to a real native Hermes `SKILL.md`; planning fails early if an asset is missing.
4. Inject the learning contract into the task and its dispatch instruction.
5. Require the worker to call `skill_view(name)` for every assigned local skill before task actions and return an `[A2A_SKILL_USAGE]` receipt.
6. Preserve the contract when large-project coordinators embed their child task graph.
7. Validate that every task has at least one profile and that every referenced profile exists.
8. Require workers to apply the bound knowledge and loaded skills to their normal owned artifacts; a profile name alone is not evidence.
9. Keep legal, security, product-specification, and licensing claims subject to official verification.
10. When a load fails, preserve passed work, use the embedded bounded role knowledge, repair the route, and retry only the affected task instead of stopping the project.
11. After verified work, classify any discovery as temporary task state, durable fact, or reusable procedure. Keep temporary state in the conversation, save durable facts with `memory`, and save only proven, non-duplicate reusable procedures with native `skill_manage`.
12. New procedural discoveries start as agent-created candidate skills so Hermes usage telemetry and Curator can manage them. Promote a candidate into the installer-controlled company skill root only after repeated successful use and independent validation.

## Pitfalls

- Do not copy third-party skill packages into the product merely because a report mentioned them.
- Do not treat upstream skill names as installed Hermes skills.
- Do not duplicate these procedures into `MEMORY.md`; Hermes memory is for durable declarative facts, not workflows.
- Do not create 14 Curator-managed user skills for this company asset. Keep the maintained registry and bundled A2A skills in the installer-controlled external root.
- Do not create a skill for one-off task progress, outputs, file hashes, or temporary checklist state.
- Do not patch a stable company skill from a leaf worker merely because one project differed; record a candidate until reuse is proven.
- Do not assign every profile to every worker; match the worker's actual responsibility.
- Do not replace project-specific evidence with generic learned rules.
- Do not block the whole pipeline for one failed learning item; preserve passed task artifacts and repair the affected task only.

## Verification

- Every task has a non-empty `learning_contract.profile_ids` list.
- Every task dispatch includes `[A2A_LEARNING_PROFILES]` and `[A2A_REQUIRED_LOCAL_SKILLS]`.
- Every task dispatch includes `[A2A_NATIVE_SKILL_LOAD]`, an explicit `skill_view(name)` instruction, and an `[A2A_SKILL_USAGE]` receipt contract.
- Every profile has knowledge, local skills, expected artifacts, a GPU policy, and an evidence rule.
- Every required local skill resolves to a real `SKILL.md` under the configured A2A external skill root.
- Every worker receipt classifies self-improvement as `none`, `created`, or `patched`; created candidates are visible in native Hermes skill usage telemetry and Curator.
- The plan's registry hash matches the maintained registry.
- All 14 approved team profiles are present in the registry.

