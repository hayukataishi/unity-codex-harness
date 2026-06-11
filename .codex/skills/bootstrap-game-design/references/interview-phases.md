# Initial Design Interview Phases

Use these phases in order, but revisit earlier phases when a later decision
creates a contradiction. Ask only the questions required for the current
target milestone.

## Milestone depth

| Milestone | Required depth |
|---|---|
| Concept | Vision, audience, central experience, scope boundaries, broad platform assumptions |
| Prototype | One testable core loop, controls, win/fail, minimum art/readability direction, Small architecture default unless evidence requires more |
| Vertical Slice | Representative content flow, production art direction, save decision, performance budget, repository/build workflow, key cross-cutting decisions |
| Alpha | Full feature and content scope, complete scene/data/save design, adopted services, migration and diagnostic strategy |
| Beta | Content-complete behavior, compatibility, accessibility/localization, performance and release risks |
| Release | Store/platform details, release Build Profiles, compliance, operations, support and rollback |

`保留` is allowed only when the decision is not required at the target
milestone and has an owner plus a later milestone or date.

## Dialogue lanes

Every question and evidence row must identify one lane.

| Lane | Meaning | Typical outputs |
|---|---|---|
| `STANDARD_RECOMMENDED` | Explain and decide a binding HREQ's project-specific applicability or method | HREQ conformance, adopted method, `対象外`, `例外承認` |
| `GAME_SPECIFIC` | Decide the individual game's experience and specification | concept, mechanics, content, presentation, design IDs, ACs |
| `MIXED` | A standard requirement constrains a game-specific decision | synchronized HREQ record and detailed game design |

Do not replace one lane with the other. For example, selecting
`HREQ-ARCH-001: Small` does not define the core loop, and describing a saveable
progression loop does not resolve `HREQ-SAVE-001` recovery and migration
decisions.

## Phase depth by milestone

`Required` means the phase must reach human approval. `Scoped` means only the
listed decisions are required and later decisions may be deferred. `Optional`
means ask only when existing evidence makes the phase relevant.

| Phase | Concept | Prototype | Vertical Slice | Alpha and later |
|---|---|---|---|---|
| 00 Session | Required | Required | Required | Required |
| 01 Vision | Required | Required | Required | Required |
| 02 Player context | Scoped: broad device and delivery assumptions | Required: target device, input, screen context, prototype delivery target | Required | Required |
| 03 Core loop | Scoped: testable loop hypothesis | Required: one complete loop and binary ACs | Required | Required |
| 04 Presentation | Optional | Scoped: control and minimum readability direction | Required | Required |
| 05 Technical baseline | Optional | Required: exact Unity version, project/render baseline, smallest architecture | Required | Required |
| 06 Save and content | Optional | Scoped: decide whether the prototype needs progress/settings persistence; later design may be deferred | Required | Required |
| 07 Production and build | Optional | Scoped: repository safety and repeatable Development build path | Required | Required |
| 08 Cross-cutting | Scoped: identify only blockers to concept validity | Scoped: decide rows that affect prototype dependencies/data; defer the rest with owner and milestone | Required: review every row | Required |
| 09 Approval | Required | Required | Required | Required |

Do not mark a whole phase `対象外` merely because only part of it is deferred.
Approve the milestone-scoped output and link the deferred decisions.

## Phase 00: Session and milestone

Lane: `MIXED`

Purpose: establish who decides, how far this session must go, and what existing
material is authoritative.

Outputs:

- project name and decision owner
- current and target milestone
- existing prototype, pitch, references, constraints, and approved decisions
- session status and current phase

Start with:

1. What game idea or existing project are we designing?
2. What milestone should this design support now?
3. Who makes final product decisions?

## Phase 01: Vision and scope

Lane: `GAME_SPECIFIC`

Purpose: define the player promise before technical choices.

Design sheet:

- concept
- genre and audience
- central experience and differentiation
- play-session length and return motivation
- explicit non-goals
- win, fail, interrupt, and end conditions

Do not accept genre labels as a substitute for observable player experience.

## Phase 02: Player context and delivery constraints

Lane: `MIXED`

Related requirement: `HREQ-PLATFORM-001`

Purpose: understand where and how the player will play before selecting a
technical configuration.

Explain and decide:

- primary and secondary platforms
- input devices
- orientation, reference resolution, and aspect-ratio range
- store or delivery channel
- device classes, play context, and known distribution constraints

Ask about the player's actual device and context. Record broad assumptions
early, but defer exact Unity version, Build Support, SDK, render pipeline, and
performance budgets to Phase 05 after the core loop and presentation needs are
known.

## Phase 03: Core loop and mechanics

Lane: `GAME_SPECIFIC`

Purpose: turn the idea into testable player actions and outcomes.

Design sheet:

- core loop
- mechanics and their inputs, rules, results, and rewards
- resources, parameters, formulas, limits
- progression and difficulty
- gameplay states and transitions

For Prototype, prioritize one complete loop over a broad feature list.
Create design IDs and binary ACs for the first implementable behavior.

## Phase 04: Presentation and interaction

Lane: `MIXED`

Related requirements: `HREQ-ART-001`, `HREQ-CAMERA-001`

Purpose: decide how the player perceives and controls the game.

Explain and decide:

- 2D, 3D, or Hybrid and render pipeline
- art direction, readability, animation, and asset constraints
- camera behavior and whether Cinemachine is used
- input actions and rebinding requirements
- UI technology, screens, navigation, resolution behavior
- audio, music, feedback, and Timeline or cutscene needs

For conditional requirements, record adopted details or a justified
`対象外` with reevaluation trigger.

## Phase 05: Technical baseline, shape, and Unity assets

Lane: `MIXED`

Related requirements: `HREQ-PLATFORM-001`, `HREQ-PROJECT-001`,
`HREQ-ARCH-001`

Purpose: choose the smallest structure that supports the current scope.

Explain and decide:

- exact Unity Editor version and source
- required Build Support and external SDK constraints
- 2D, 3D, or Hybrid baseline and render pipeline
- target FPS and initial performance budget
- `Small`, `Standard`, or `Large` architecture profile
- reason, dependency direction, composition, and migration triggers
- project folder and asmdef application
- game flow, scenes, and loading
- Prefabs, ScriptableObjects, components, tags, layers, and collision rules

Recommend `Small` for a narrow prototype unless team, lifetime, module, or
platform constraints justify more. Do not introduce speculative abstractions.

## Phase 06: Persistence, data, and content delivery

Lane: `MIXED`

Related requirement: `HREQ-SAVE-001`

Purpose: separate runtime state, configuration, progression, and content.

Explain and decide:

- whether progress is saved
- save fields, stable IDs, format, location, and platform scope
- atomic write, backup, corruption recovery, schema migration, downgrade
- cloud conflict, privacy, security, and key-management dependencies
- ScriptableObject and external master-data ownership
- Addressables adoption, groups, labels, and update model

If the game has no progression save, record what is still stored, such as
settings, and why the full save requirement is not applicable.

## Phase 07: Repository, production, build, and diagnostics

Lane: `MIXED`; most workflow choices begin from standard-recommended HREQs,
while build contents and diagnostic needs are game-specific.

Related requirements: `HREQ-REPO-001`, `HREQ-BUILD-001`

Purpose: make the design producible and releasable by the actual team.

Explain and decide:

- branch and review workflow
- Visible Meta Files, serialization, UnityYAMLMerge
- LFS criteria, locks, asset owners, quotas, and CI availability
- Development, QA, and Release Build Profiles
- build output, defines, scenes, clean-build policy
- profiling budgets, logging, diagnostics, debug and cheat controls

Do not prescribe a branch model or LFS extensions without repository evidence.

## Phase 08: Cross-cutting product decisions

Lane: `MIXED`

Related requirement: `HREQ-CROSS-001`

Purpose: make adoption and non-adoption explicit before dependencies or data
flows appear.

At Vertical Slice and later, review every matrix row. At Concept or Prototype,
first identify rows that can affect the current milestone's dependencies,
data, feasibility, or player experience; defer the rest with owner and target
milestone.

- accessibility
- localization
- multiplayer and online
- account, authentication, and cloud save
- analytics and crash reporting
- privacy, consent, and compliance
- security and abuse prevention
- LiveOps and remote config
- IAP, ads, and entitlements
- moderation and community
- modding and UGC
- XR
- performance and device budgets
- diagnostics and debug controls

For each row, record `採用`, `不採用`, or `保留`. Explain why it matters,
what data or dependencies it introduces, and when it must be revisited.
High-impact legal, privacy, monetization, account, online, UGC, and target
region decisions require explicit human approval.

## Phase 09: Traceability and approval

Lane: `MIXED`

Related requirements: `HREQ-DESIGN-001`, `HREQ-VALIDATION-001`

Purpose: turn the agreed design into an implementation-ready contract.

Confirm:

- every first implementation unit has a stable design ID
- every active design ID has binary ACs and verification types
- subjective ACs are assigned to human review
- contradictions and unresolved questions have owners and deadlines
- HREQ states and exceptions match the detailed sections
- design review state and approval history are current
- the user explicitly approves the target-milestone design

Run the final subagent audit before marking the session complete.
