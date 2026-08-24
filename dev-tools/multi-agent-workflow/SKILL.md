---
name: multi-agent-workflow
description: >-
  Use for non-trivial implementation, debugging, refactoring, configuration,
  or review work in DeepSeek Harness when independent preparation and
  verification reduce risk. Map Preflight, Builder, Reviewer, and optional
  Sol-Max roles onto the DSH subagent tools that are actually available. Keep
  the current Agent responsible for edits, decisions, validation, and delivery.
---

# Multi-Agent Workflow for DeepSeek Harness

This is an operating procedure for DSH. The four role names are workflow
labels, not built-in DSH services or tools. Implement them with the tools exposed
in the current session, and never invent a provider or a tool name.

## DSH Facts That Constrain the Workflow

- When the filesystem skill provider is mounted, a project skill under `.agents/skills/<name>/SKILL.md` is discovered by DSH for the current workspace. The directory name and
  frontmatter `name` must match. The catalog exposes only the frontmatter
  summary; the `skill` tool loads this full body on demand. Updating the file is
  a skill-catalog change, not an executable workflow registration.
- In the normal DSH presets, `subagent` and `subagent_fork` are separate
  model-facing tools backed by the `spawn` and `fork` providers. A deployment may
  omit either tool, change its background policy, or expose another provider
  tool such as `subagent_codex`; inspect the current tool catalog and use only
  names actually present.
- `spawn` creates a fresh child session with its own context. `fork` creates a
  child seeded with the parent's completed session prefix; the current
  in-flight turn and its unbalanced tool call are not included. A fork is not a
  way to pass the current turn's hidden context.
- Both `subagent` and `subagent_fork` inherit the parent Agent's STATIC
  `parent.options` provider/model/maxTokens route via `resolveChildAgentOptions`,
  NOT the runtime model the current session may have switched to through model
  selection. The current turn's dynamic route and the child's inherited route
  can therefore differ; do not assume the child runs on the model you are
  currently using.
- Neither `subagent` nor `subagent_fork` exposes a per-call `provider`/`model`
  field. Their tool schema only carries the prompt and scheduling fields, so a
  single call cannot override the inherited route. The `workflow` tool's
  `agent(prompt, { provider, model })` hook is the model-facing way to start a
  child on an explicit route.
- Background behavior is configuration-dependent. A continuable child returns a
  durable `subagentId` and can receive `send_message`; a one-shot background
  call returns a job id that is collected with `job_output`. Do not assume that
  every `subagent` call supports one route. Read the returned shape and the
  tool's current description.
- `send_message` queues a later turn for a continuable child. `report` exists
  only in deployments that install the continuable child report setup, and only
  the direct parent receives it. For a background continuable child, finishing
  with `done` does not automatically transfer its transcript, tool output, or
  reasoning; use `report` when available or collect the configured runtime
  result.
- DSH does not provide per-call `isolation` for these model-facing delegation
  tools. A `toolFilter` is a composition-time setting on a delegation tool row,
  not a field the model can safely add to one call. A prompt saying "read-only"
  is therefore an operating rule unless the current composition has a genuinely
  filtered delegation tool. Never claim that Preflight or Reviewer was
  sandboxed when it was only instructed not to write.
- The `workflow` tool is for an explicit workflow request or large fan-out. Its
  plain-JavaScript script only coordinates agents: it has no filesystem,
  network, timers, or Node.js APIs. Agents must perform repository work. Its
  result must be JSON-serializable; unsupported hook arguments or schemas fail
  the whole script. It is also the model-facing way to override a child's
  provider/model with `agent(prompt, { provider, model })`. For one or two
  delegations, use ordinary `subagent` calls; when those need a specific route,
  use `workflow`'s `agent()` override instead.
- `ralph` is a separate fresh-agent iteration mechanism and is not a synonym for
  this workflow. Use it only when the human explicitly asks for a Ralph loop.
  Use a same-session goal for a long-running objective, not to simulate the
  Preflight/Reviewer stages.

## Choose the Smallest Mode

Use the full pipeline for work with a meaningful change surface or risk:

- multiple files or components;
- public contracts, persistence, migrations, security, concurrency, or release
  behavior;
- a bug whose root cause is not established;
- a refactor or review where an independent reading adds useful evidence.

For a factual answer, a trivial one-line change, or work whose verification is
obvious, execute directly. Do not spend four Agent calls to create ceremony.

Use a normal foreground `subagent` call when the next stage needs its result.
Use `subagent_fork` only when the inherited completed conversation is useful and
it is available; otherwise give `subagent` a complete standalone prompt. A
role's model is replaceable: the role is not tied to a provider named
`Sol-Max`.

## Role Mapping in DSH

| Role | DSH implementation | What it may do | Required output |
| --- | --- | --- | --- |
| **Coordinator** | The current top-level Agent | Route stages and retain ownership | Handoffs and final decision |
| **Preflight** | A foreground `subagent` or current Agent read pass | Inspect context only; do not mutate | Engineering brief |
| **Builder** | The current top-level Agent by default | Use normal repository tools to edit and validate | Actual diff and evidence |
| **Reviewer** | A separate foreground `subagent` or `subagent_fork` | Read the actual diff and evidence; do not mutate | `PASS`, `CHANGES_REQUIRED`, or `INCONCLUSIVE` |
| **Sol-Max** | An optional separate subagent/provider selected from the live catalog | Answer one concrete difficult question | Recommendation and missing facts |

The Builder is not replaced by the reviewer or specialist. The original human
request outranks every generated brief and recommendation. The Builder decides
what to adopt, makes the final changes, runs validation, and answers the user.

A delegation that fails is a failed stage, not a failed outcome. Prefer the
cheapest working transport: a foreground `subagent` or `subagent_fork`; when the
inherited route is unavailable, start the role through `workflow`'s `agent()`
with an explicit `{ provider, model }`; when no child transport works, fall back
to the current Agent and report that the independent boundary could not be
enforced. Do not mark a review `PASS` when the Reviewer never returned a result.

## Stage 1: Preflight

If delegating, use a foreground call because Builder needs the result before
acting:

```text
description: "Preflight brief"
prompt:
  You are the read-only Preflight stage for a DSH coding task.
  Original user request: <unchanged request>
  Inspect the workspace with read-only tools available in your session.
  Do not use write, edit, or mutating commands. This boundary is prompt-level
  unless the host composition explicitly provides a filtered child tool.
  Return only this brief:

  Goal:
  Scope:
  Non-goals:
  Acceptance criteria:
  Relevant files, entry points, or context:
  Risks:
  Open questions:
run_in_background: false
```

Use the available DSH read tools such as `read`, `glob`, and `grep`. A shell
command is not read-only merely because the prompt calls it that; avoid `bash`
for Preflight unless the command is clearly non-mutating. Unknown facts stay
unknown. The brief organizes the request and does not authorize scope changes.

## Stage 2: Builder

The current Agent receives the unchanged request and the brief. Before editing:

1. inspect the actual entry path, callers, neighboring implementations,
   repository instructions, and current workspace state;
2. identify the smallest correct change and its affected consumers;
3. preserve unrelated user changes;
4. use the repository's existing tools and patterns;
5. run the narrowest meaningful validation, then broaden it when the blast
   radius requires it.

Use `read`, `glob`, and `grep` to inspect. Use `edit` for targeted replacements,
`write` for new or complete files, and `bash` for commands and tests. Follow the
current DSH file-tool policy and do not invent sandbox escalation parameters.
Record the actual files changed, commands run, results, and unresolved
uncertainty. Do not ask Reviewer to inspect a plan or an intended diff.

For non-trivial work, keep the stage state visible with `todo_write` when that
tool is available. DSH replaces the entire todo list on every call; mark work
`in_progress` while active, mark it `completed` immediately when finished, and
allow parallel active items only when the deployment permits them.

## Stage 3: Reviewer

After Builder has produced the real workspace diff and validation output, make a
separate foreground delegation when independent review is worthwhile. Prefer a
fresh `subagent` with a complete prompt so the review is not merely an echo of
the Builder's reasoning. A `subagent_fork` may be used only if its inherited
completed history is useful; it still cannot see the Builder's current
in-flight turn, so include the actual diff and evidence explicitly.

```text
description: "Review actual diff"
prompt:
  You are the read-only Reviewer for a DSH coding task.
  Original goal: <goal>
  Acceptance criteria: <criteria>
  Actual diff: <diff or precise changed paths>
  Validation evidence: <commands and results>
  Known limitations: <limitations>

  Inspect the changed files and the surrounding code needed to verify behavior.
  Do not use write, edit, or mutating commands. This is prompt-level unless a
  filtered delegation tool is explicitly available.
  Return exactly one top-level verdict:
  PASS
  CHANGES_REQUIRED
  INCONCLUSIVE
```

The verdict means:

- `PASS`: acceptance criteria are met and the evidence is sufficient;
- `CHANGES_REQUIRED`: name each concrete defect, regression, missing requirement,
  or inadequate check, with severity, evidence, and the smallest correction;
- `INCONCLUSIVE`: state the exact missing evidence or unavailable environment
  capability and whether Builder can obtain it.

A Reviewer does not edit files, approve its own changes, silently redefine the
request, or claim a check passed when it did not run.

## Stage 4: Repair and Optional Escalation

For `CHANGES_REQUIRED`, or for actionable `INCONCLUSIVE` findings:

1. return the findings to Builder;
2. let Builder decide and make the correction or obtain the missing evidence;
3. run validation again;
4. send the new actual diff and results to Reviewer.

Repeat until `PASS`, or report the concrete blocker. Do not hide a remaining
`INCONCLUSIVE` verdict.

`Sol-Max` is only a role label. Use it only for one named question that the
Builder cannot resolve efficiently, such as a concrete validation failure with
competing causes, a security or persistence risk, a public-contract decision,
or a direct human request for specialist advice. Select an actually exposed
`subagent*` tool/provider; do not assume `subagent_codex`,
`subagent_claude_code`, or any other optional provider exists.

Send the minimum redacted context:

```text
Question:
Known facts:
Relevant evidence:
Constraints:
Decision needed:
```

Never send secrets, credentials, complete transcripts, provider configuration,
or unnecessary private paths. Sol-Max advises; it does not edit or own the
final decision. Builder records whether the advice was adopted and validates
the resulting change.

## Diagnosing a Failed Child

`subagent run failed` is a normalized headline, not the root cause. The
model-facing delegation tools collapse the child's terminal reason and do not
surface the underlying model error. To recover evidence:

1. Find the child session under `<workspace sessions dir>/<childId>/`, keyed by
   the workspace-scoped session directory (for the default workspace this is
   typically `~/.dsh/sessions/--<escaped-workspace>--/<childId>`). The exact path
   can be derived from the workspace the session ran in.
2. Decompress `session.jsonl.zstd` (`zstdcat` when available) and read the last
   `turn/end` event: its `data.reason.error` carries the real message and code,
   and `request/header` events record the provider/model the child actually
   used. This distinguishes a bad inherited route (`400 invalid codex request`
   or similar) from a prompt, permission, or composition failure.
3. Read the inherited route from the child's `request/header.config`. When it is
   not the current session's dynamic route, the failure is the static
   `parent.options` route, not the model you are talking through.

Use the evidence to pick a remedy rather than retrying blindly:

- If the inherited route is unavailable, start the child through `workflow`'s
  `agent(prompt, { provider, model })` with a route known to work, or fall back
  to the current Agent and state which boundary could not be enforced.
- Do not treat a failed delegation as a `PASS`, and do not retry the same
  delegation with the same inherited route expecting a different result.

## Background Children and Cleanup

Use background delegation only when the current Agent can continue useful work:

- A returned durable `subagentId` belongs to a continuable child. Wait for the
  runtime's settlement notice, use `send_message` for its next turn, and use
  `list_agents` to inspect direct children or the descendant tree when needed.
  The child should call `report` once with a self-contained result when that
  tool is available; otherwise collect the runtime's final message.
- A returned job id belongs to a one-shot background task. Collect it with
  `job_output`; use `job_kill` only when it no longer matters or must be
  cancelled.
- `interrupt_agent` stops only the target's current turn. Queued messages and
  descendants may remain active, so it is not equivalent to killing the whole
  tree.

Track every started background job or child. Before final delivery, collect
relevant results, cancel work that no longer matters, and do not leave a
necessary background operation running. A failed child may provide partial
output; treat it as failed evidence, correct the prompt or provider choice, and
retry only when the task still needs that role.

## When to Use `workflow`

Use DSH's `workflow` tool only for a user-requested workflow or genuine
large-scale fan-out, such as reviewing many independent files. The tool call
contains a JSON `meta` block and a plain JavaScript `script`; do not put
`export`, TypeScript, JSX, or filesystem code in the script. The script can use
`agent`, `pipeline`, `parallel`, `phase`, `log`, and `args` only. Return one
JSON-serializable value.

Prefer `pipeline` for independent multi-stage items because it has no global
barrier. Use `parallel` only when a stage genuinely needs all prior results.
Give `agent` complete prompts; it can return text or a validated object when the
supported object-rooted schema is used. Unsupported options such as
`isolation`, `effort`, or `agentType` are errors, not ignored hints. A workflow
script cannot directly inspect or edit the workspace; its child Agents must do
that, and a script failure is not a partial successful review.

For this four-role procedure, ordinary foreground `subagent` calls are usually
simpler than wrapping the entire task in `workflow`.

## DSH-Compatible Delivery Checklist

Before answering the user, Builder verifies:

- the unchanged original request still controls the outcome;
- actual changed paths and unrelated workspace changes are understood;
- validation commands and results are reported exactly;
- Reviewer returned `PASS`, or an `INCONCLUSIVE`/blocked condition is disclosed;
- any Sol-Max advice came from an actually available DSH delegation tool and was
  tied to one named question;
- all relevant background jobs and children were collected or cancelled;
- any failed delegation's root cause was read from the child session's
  `session.jsonl.zstd` (`turn/end` reason and `request/header` route) rather than
  reported as `subagent run failed`; and
- no claim of sandbox isolation, tool availability, or test success exceeds the
  current DSH evidence.

If a delegation tool, provider, child report, or workflow capability is absent,
fall back to the current Agent or manual handoff and say which boundary could
not be enforced. The final response should lead with the outcome, changed
artifacts, checks actually run, and residual risk.
