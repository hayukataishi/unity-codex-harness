---
name: bootstrap-game-design
description: Guide a user through the initial design of a Unity game, explaining required and recommended harness decisions, asking focused questions phase by phase, recording only confirmed answers in the canonical game design sheet, tracking deferred decisions, and using an independent read-only subagent audit when available. Use for new projects, incomplete design sheets, idea-to-spec onboarding, milestone planning, or requests to decide the game design comprehensively before implementation.
---

# Bootstrap Game Design

## Purpose

Run a resumable initial-design conversation that covers both inherited
`HREQ-*` decisions and game-specific design without overwhelming the user.
This Skill owns the conversation flow. Use `$maintain-game-design` for later
incremental changes after the initial design reaches its target milestone.

## Integrity gate

In an installed game project, run:

```bash
python3 scripts/unity_codex_harness/verify_harness_integrity.py \
  --project-root "$UNITY_PROJECT_ROOT"
```

Stop if it fails. In the harness source repository, run
`python3 scripts/validate_repository.py` instead.

## Required context

Read:

1. `docs/unity_harness_engineering.md`
2. `docs/unity_harness_capabilities.md`
3. `docs/unity_harness_requirements.md`
4. `docs/unity_design_sheet.md`
5. `docs/mcp_and_skills_list.md`
6. [interview-phases.md](references/interview-phases.md)
7. Repository instructions

Resolve `UNITY_PROJECT_ROOT` from `Assets/`, `Packages/`, and
`ProjectSettings/ProjectVersion.txt`.

## Conversation contract

- Ask one focused question or one tightly related group of at most three
  questions at a time.
- Before asking for a technical choice, explain its player or production
  impact, realistic options, recommendation, and important tradeoffs.
- Ask for the user's intent in open form before narrowing to options. Include
  a realistic alternative, `その他`, and `保留` when presenting choices.
- Use the user's language and experience level. Define Unity terminology when
  it first matters.
- Distinguish `確定`, `提案`, `仮定`, `要確認`, and `対象外`.
- Never convert silence, uncertainty, an example, or the harness recommendation
  into a confirmed game decision.
- Offer a recommendation when evidence supports one, but keep the user's
  decision explicit.
- Allow `保留` only with reason, decision owner, and target milestone or date.
- Summarize the proposed record after each answer. Update normative design
  sections only after explicit user confirmation. A user statement that
  explicitly says the decision is final may serve as that confirmation, but
  clarity inferred by the agent may not.
- Keep the current question, options and tradeoffs, answer summary, proposed
  record, and confirmation state in the non-normative dialogue evidence table
  so another session can resume before confirmation.
- Keep subjective decisions such as fun, tone, clarity, art appeal, and
  difficulty under human ownership.
- Do not begin implementation from this Skill.

## Session workflow

1. Inspect the initial-design progress table and resume the first unfinished
   phase. Do not restart completed phases unless the user requests review or a
   contradiction requires reopening one.
2. Confirm the target milestone. Apply the milestone guidance in
   [interview-phases.md](references/interview-phases.md); not every release
   detail must be fixed during Concept or Prototype.
3. For the active phase:
   - show why it matters now
   - identify related `HREQ-*` rows and existing game decisions
   - explain options and tradeoffs
   - ask the next focused question
   - classify and summarize the answer
   - obtain confirmation when needed
   - update the smallest relevant part of `docs/unity_design_sheet.md`
   - update the dialogue checkpoint and evidence row before yielding
4. Record deferred decisions in `未決事項` with owner and deadline or
   milestone. Mark genuinely irrelevant conditional requirements as `対象外`
   with reason and reevaluation trigger.
5. At phase exit, run the independent audit described below when multi-agent
   tools are available.
6. Mark a phase `人間承認済` only when its milestone-required outputs are
   confirmed or recorded as not applicable, and any later-milestone outputs
   are explicitly deferred with owner and target.
7. Run `validate_design_contract.py` for HREQs resolved by the phase.
8. Continue to the next phase only after giving the user a short summary of
   decisions, deferrals, and the next topic.
9. When an upstream decision changes, mark every affected approved phase
   `再検討` and list the reason before continuing.
10. At final review, check all phases, unresolved decisions, design IDs, active
    ACs, approval state, and implementation readiness. Set the session to
    `マイルストーン承認済` only after explicit user approval.

## Subagent audit

The main agent remains the only user-facing interviewer and the only writer of
the game design sheet.

When multi-agent tools are available, use `spawn_agent` to start one read-only
subagent and `wait_agent` only when its findings are needed:

- after each phase before marking it `人間承認済`
- once more before final approval
- when contradictions span multiple phases

Give it the current design sheet, applicable HREQ text, the active phase
rubric, the relevant dialogue evidence rows, and
[subagent-audit.md](references/subagent-audit.md). The evidence must include
the question, options and explained tradeoffs, answer summary, proposed
record, and confirmation state. Do not leak an intended answer that was not
shown to the user or ask the subagent to agree with the main agent.

The subagent may identify omissions, contradictions, leading questions,
unsupported confirmation, or missing tradeoff explanations. It must not edit
files, decide subjective requirements, or speak to the user directly.

The main agent reviews the findings, rejects false positives, and asks the user
only the questions needed to resolve valid findings. Record audit status in the
progress table. If multi-agent tools are unavailable, perform the same
checklist locally and record `SELF REVIEW`; do not pretend it was independent.

## Phase completion rule

A phase cannot become `人間承認済` while any of these is true:

- a milestone-required field is blank or silently assumed
- a related milestone-required decision HREQ remains `未決定`
- a conditional HREQ required at this milestone has neither an adopted
  decision nor a justified `対象外`
- a deferral lacks owner and target milestone or date
- a deferred decision is required for the current milestone
- confirmed entries contradict another section
- the subagent or self-review has an unresolved blocking finding
- the user has not confirmed a subjective or high-impact choice
- a changed upstream decision has not reopened affected downstream phases

## Writing rules

- Write game decisions only to `docs/unity_design_sheet.md`.
- Treat `初期設計対話`の`対話チェックポイント` and `対話証跡` as
  non-normative resume and audit records. Never treat unconfirmed evidence as
  a game requirement or implementation approval.
- Update `初期設計対話`, related HREQ conformance rows, affected design
  sections, `未決事項`, and approval history together.
- Use `$maintain-game-design` conventions for design IDs and acceptance
  criteria.
- Do not copy `HCAP-*`, harness regression results, or explanatory examples
  into the game design sheet.
- Preserve issued IDs and approved decisions. Reopen them explicitly instead
  of silently replacing them.

## Handoff

The final handoff must state:

- target milestone and session status
- completed and reopened phases
- confirmed HREQ decisions and approved exceptions
- unresolved decisions with owners and deadlines
- approved game-specific design IDs and ACs
- independent audit status or `SELF REVIEW`
- whether implementation may begin, and which design unit is ready first

Use `$report-unity-work` for the human-reviewable final report.
