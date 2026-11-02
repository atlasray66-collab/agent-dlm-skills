# DLM Outcome Governance

This is the upper constraint for the DLM lifecycle. Apply it before lifecycle-specific conventions. It changes how DLM work is selected, allowed to block, evidenced, reviewed, synchronized, released, and stopped; it does not require a separate governance artifact, score, authority JSON, hash chain, checker, receipt, audit, or subagent unless a real consumer, accepted contract, or material risk requires one.

## Core outcome principle

Repository work exists to make the user-requested target state true and to reduce relevant uncertainty enough for a reliable decision. Implementation, tests, documentation, evidence, audit, metadata, and process are instruments. None substitutes for the target itself.

Documentation or governance is target work when the user requested that state. Otherwise its value depends on a real consumer, decision use, accepted contract, or material risk.

Apply these principles:

- **Causal relevance**: every material action advances the target state, verifies a completion-relevant claim, or prevents a concrete material risk. Defer or remove work with no such causal link.
- **Claim-evidence fit**: prefer evidence from the layer that most directly proves or disproves the claim. Runtime, contract, and coordination claims normally use their corresponding evidence. A cross-layer substitute must explain why it is sufficient for the current decision.
- **Proportional rigor**: scale planning, validation, rollback, and independent review to consequence, uncertainty, irreversibility, and blast radius—not labels, artifact counts, process tradition, or reviewer preference.
- **Criterion integrity**: completion criteria come only from the user outcome, applicable contracts, accepted constraints, and material safety boundaries. Tools, processes, and reviewers cannot silently add criteria.
- **No proxy optimization**: reports, statuses, checklists, hashes, green checks, and documentation completeness are indicators or coordination aids. Improving them without changing the target state or material uncertainty is not progress.
- **State-layer separation**: target state, evidence state, and coordination state are independent. Synchronize them only when a real consumer or decision depends on the relationship. One layer cannot impersonate or invalidate another without demonstrated impact on the current decision.
- **Marginal convergence**: once the target is true and remaining material uncertainty is acceptably bounded, further work requires a specific unresolved risk or contradiction. Repetition without new information is not additional rigor.
- **Compute follows expected return**: choose the next action by expected contribution to the target or reduction of material uncertainty. When process activity consumes the main effort without proportional risk reduction, return effort to the underlying target work.

## Lifecycle application

| DLM stage | Required application |
|---|---|
| Load | Perform one combined identity/scope safety check, then load the minimum context needed for the next material decision. Do not repeat Session Init or let unrelated administrative gaps delay target work. |
| Plan | Define the intended outcome, Draft Acceptance Baseline, Authorized Scope, claim-matched evidence, material risks, dependencies, and stop line. Remove work with no causal role. |
| Build/maintain DLM | Treat knowledge artifacts as target work only when the requested state or a real consumer needs them. Health indicators cannot stand in for knowledge usefulness or engineering truth. |
| Reflect/audit | Measure only the accepted/Frozen criteria. Formal independent review requires user request, accepted contract, or demonstrable risk benefit. Findings without baseline impact are Advisory. |
| Sediment | After the result stabilizes, reuse existing evidence and synchronize only knowledge/state consumers actually need. Sediment does not retroactively decide engineering completion. |
| Version/release/close | Keep engineering, release evidence, coordination, Git, deployment, and field states separate. Verify only claims required by the authorized release baseline. |
| Delegation | Delegate independent, nonconflicting work within existing task authority, using a complete task card and stop line. Follow current host/tool rules for subagents and user-owned tasks. Delegation is not a proxy for rigor. |

## Work classes and blocking authority

Classify planned work by causal role, not filename or task label:

- **Target work** directly changes the requested code, architecture, contract, runtime behavior, data, documentation, or governance state. Failure may block completion when the corresponding target or applicable contract is unmet.
- **Substantive assurance** directly verifies a completion claim or prevents a concrete material risk. Examples include necessary tests, runtime observations, safety checks, and protections against writer collision, unauthorized writes, wrong repository identity, or irreversible actions. Failure blocks only when its material impact on the current target is demonstrated.
- **Administrative record** synchronizes status, repeats explanations, changes timestamps or display order, or maintains records that no product, release, acceptance, or decision consumer reads. It cannot block the target, change a substantive acceptance conclusion, or trigger a rebuild, retest, full audit, or independent review.

A receipt, manifest, hash, report, or other record is substantive evidence only when a named consumer exists and it directly supports the current completion claim. Do not invent a consumer, checker, or synonymous second evidence record merely to prove process compliance.

## Convergent execution sequence

1. **Set target and boundary once**: identify the intended state, authority, applicable criteria, main risks, and stop line. Existing Baseline Owner or named-queue authorization is recorded once; do not repeatedly ask, refreeze, or manufacture proof of authorization.
2. **Advance the shortest causal path**: after one necessary combined writer/scope safety check, inspect actual facts and perform work that directly changes the target state. Do not generate consecutive process artifacts or start a review chain before the first effective target advance.
3. **Validate with matching evidence**: select compilation, tests, contract checks, runtime observations, or real workflows that directly support the claim. When validation fails, repair target work before polishing administrative material.
4. **Synchronize once for real consumers**: after the result stabilizes, reuse existing evidence and update only status, receipts, handoffs, or indexes a real consumer requires. Pure record changes do not reopen unrelated validation.
5. **Use independent review only for material risk**: ordinary work defaults to targeted acceptance by the implementer. Use formal independent review only when the user requests it, an accepted contract requires it, or consequence, uncertainty, irreversibility, and blast radius demonstrate value.

Before target work makes effective progress, allow at most one combined control-plane preflight. Record non-safety administrative gaps for closeout instead of letting them occupy the causal path.

## Acceptance Baseline lifecycle

An Acceptance Baseline has three states:

```text
Draft -> Frozen -> Verified
```

- Planning may create and revise `Draft`.
- Before substantive execution, formal audit, execution-capable delegation, or an external-state mutation, the Baseline Owner makes one `Frozen` decision.
- Mark `Verified` and stop when every Frozen criterion passes, required evidence is valid, and the stop line is reached.

The baseline may live in the task body or explicit session authorization. Do not create a separate authority artifact unless an existing machine consumer requires it. It contains:

- applicable SSOT/L0;
- one intended outcome and explicit non-goals;
- an `Authorized Scope` that separately states allowed reads, allowed file writes, allowed external actions, and allowed state/resource mutations; write `none` where inapplicable;
- uniquely referenceable acceptance criteria;
- required claim-matched evidence;
- a stop line;
- the Baseline Owner.

If no owner is separately named, use the user or primary agent consistently with existing authority; this default never grants new mutation authority. Once Frozen, implementers and auditors cannot add, remove, or change criteria.

If the owner pre-authorized a named queue, baseline adjustment, or freeze action, proceed within that authority without repeated requests or repeated evidence that authorization exists.

### Semantic identity and byte-exact evidence

`Frozen` is a governance decision, not a state inferred from hashes, checkout representation, encoding, or line endings. EOL-only, UTF-8 BOM, or Git clean/smudge representation changes do not return a baseline to Draft and are not `Baseline invalidation`.

Use identity at the level the claim requires:

- **Semantic snapshot** for task content: decode as UTF-8, remove BOM, normalize line endings to LF, and normalize paths to repository-relative `/`.
- **Byte-exact evidence hash** only when acceptance explicitly requires raw-byte integrity, such as CLI I/O, binaries, screenshots, or a manifest/report/receipt whose bytes are themselves evidence.

Do not use a raw hash to stand in for Frozen status or the semantic identity of an entire source tree.

Stop and report `Baseline invalidation` only when new facts show that the Frozen baseline conflicts with SSOT, rests on false facts, or would create a safety or data-loss risk. Continue only after explicit recalibration by the Baseline Owner.

## Audit measures only the Frozen error boundary

Deep or Anchored work does not imply independent audit for every Subtask. Routine batches that change public APIs or schemas should normally use contract and compatibility tests; reserve full independent audit for an aggregation or release gate when its risk benefit is demonstrated.

A formal audit:

- returns `PASS` or `FAIL` against each Frozen acceptance criterion;
- is not an open-ended search for every possible improvement;
- does not require zero comments for completion;
- cannot replace an accepted implementation with a reviewer preference when both satisfy SSOT, Frozen criteria, safety, and compatibility.

A blocking Finding provides all of:

1. the violated Frozen criterion or SSOT clause;
2. direct evidence, a reproducible counterexample, a locatable contradiction, or a failed observation;
3. the actual effect on the current outcome;
4. proof that the issue belongs to the current Authorized Scope.

Anything that cannot establish those elements is `Advisory` or `Deferred Finding`, regardless of severity labels. Out-of-scope findings do not enter the current repair loop. If one exposes safety, data-loss, or SSOT-foundation failure, report `Baseline invalidation` instead of expanding scope through a severity label.

After a repair, retest only the original failed condition and its direct regression surface. Do not start another unbounded full audit.

Treat raw-byte differences through `.gitattributes` and Git normalization first. If `git diff --ignore-space-at-eol`, normalized text, or equivalent semantic comparison proves the difference is only EOL/BOM, the audit snapshot remains valid and the full-audit budget is not consumed again. Only semantic source, task-contract, execution-result, or explicitly byte-exact evidence changes make a snapshot stale.

Batch encoding/EOL repair once after implementation writes and before the fixed audit snapshot. EOL-only repair during audit does not reopen full build/test/audit; a semantic diff follows normal snapshot-change rules.

## Revalidation and convergence limits

- Perform at most one formal full audit for one stable target state.
- After fixes, revalidate failed conditions and direct regressions only.
- Do not audit the audit, repeat proof without new information, or reopen full validation because administrative records changed.
- Do not establish time ratios, artifact quotas, or check counts as proxy metrics.
- If governance or audit consumes the main effort without proportional material-risk reduction, stop adding governance and return to target work.
- Do not invent decision lines, quality gates, or implicit completion criteria. Outside applicable SSOT, safety boundaries, and Frozen criteria, new suggestions are Advisory and cannot force a switch between otherwise valid implementations.

## Completion and named queues

When all Frozen criteria pass, required evidence holds, and the stop line is reached, mark the baseline `Verified` and end the task. Further possible optimization is not a reason to continue.

After completion, do not automatically start the next Subtask, claim the next work item, or implement a Deferred Finding. Require explicit authorization from the user or relevant Baseline Owner.

One authorization may cover a **named, ordered, bounded queue** only when it records:

- queue boundary and order;
- an independent baseline for each item;
- entry and exit conditions;
- dependency order;
- a shared stop gate;
- non-overlapping write sets or an explicit collision group.

Such authorization permits sequential activation without asking again for every item; it does not merge write scopes or permit concurrent writers in one collision group. If an item changes its intended outcome, acceptance criteria, Authorized Scope, write set, external actions, dependencies, or stop line, return that item to Draft and stop continuous execution until the owner recalibrates it. Stop when the queue completes, reaches a declared human gate, or triggers Baseline invalidation.

## Delegated/subagent task cards

Use subagents when an independently acceptable unit can run alongside useful primary-agent work and is likely to save time or improve confidence. Existing task authorization covers ordinary delegation within that scope when current host/tool rules permit it; do not add a separate user confirmation solely because another agent performs the work. A user-owned Codex task is a separate action and requires the explicit creation intent required by its tool. Formal independent audit still requires the admission basis defined above.

Every delegation task card repeats:

- one intended outcome;
- SSOT and the Acceptance Baseline;
- Authorized Scope;
- explicit prohibitions;
- deliverables;
- claim-matched acceptance evidence;
- stop line;
- the action after completion.

Do not delegate with open-ended instructions such as “review everything” or “improve as much as possible.” Delegates are read-only by default; writing, external actions, or state/resource mutation require explicit task-card authority. One file, resource, or work item has at most one writer at a time, and an audit delegate cannot modify the object it audits.

A delegate cannot expand scope or switch to an adjacent task. Nested delegation follows current host/tool rules and the parent task card; any child receives a narrower, nonconflicting scope and the same prohibitions. The primary agent remains responsible for integration and claim-matched acceptance. Report out-of-scope discoveries to the primary agent for disposition.
