# Evidence, dependencies, and bounded decisions

Use the relevant section when a DLM decision depends on evidence reuse, repeated failure, changing knowledge, or a long-task resume. This reference refines the existing outcome governance; it adds no mandatory artifact, service, model call, approval, or completion criterion. Keep DLM 7 and manifest schema 2. Existing task notes and L2 sections are sufficient.

## 1. Bind a claim to an actual observation

Use the existing AC ID or a stable L2 section anchor. For a consequential claim, make its result traceable to:

- the observed result: `proven`, `disproven`, or `unknown`;
- the original evidence location and the object actually checked;
- the revision/build, configuration, environment or hardware conditions that can change the conclusion;
- the part of the criterion still unproven and the smallest useful next observation.

Fill only distinctions that matter to the claim. A local file, command output, existing test report or UI observation can be sufficient; do not create a second receipt. A reference, nonempty file, valid status, queued job or exit code alone does not establish behavior. Keep contrary observations visible. An observation made on an older revision remains a historical fact; its applicability to a changed target must be established separately.

At closure, map actual results to the accepted ACs in the task or existing review. If a required result is missing, report `unknown`; do not derive PASS from metadata. A changed evidence dependency can require focused revalidation without changing the Frozen criteria. Owner recalibration is required only for the baseline changes defined by outcome governance.

## 2. Make knowledge reuse conditional

For knowledge that is likely to drift, record the applicable version/configuration/environment, the source or evidence anchors, and which changes require review. Use a stable existing section anchor rather than introducing an ID catalog. A useful relationship is:

`source/configuration/observation -> knowledge claim -> current decision or AC`

Record only relationships used by a real loading or decision consumer. Keep facts, inferences, and owner decisions distinguishable. When new evidence contradicts a claim, identify whether its assumptions changed, it was superseded, or it was wrong. Correct authorized knowledge in its existing location and retain a replacement pointer when readers may encounter an obsolete entry. Do not append an incompatible second truth.

### Optional document-level impact hints

L2 front matter can add `depends_on` alongside existing `match_globs`:

```yaml
match_globs:
  - "src/Calibration/**/*.cs"
  - "config/camera.json"
depends_on:
  - "doc_llm/Domains/vision/L2_Modules/coordinate-system.md"
```

`depends_on` lists existing repository-relative L2 documents whose knowledge is used by this document. It is optional; omit it or use `[]` when not useful. Keep direct source/configuration dependencies in `match_globs`. Use `/` paths and simple quoted scalar/list metadata as supported by the route parser; do not introduce nested YAML structures. Personal skills, adjacent projects and external sources never enter these path fields. External provenance can remain in prose under existing read authorization.

The optional `dlm-load/scripts/dlm_impact.py` reads an explicitly supplied changed-file list and reports direct and transitive document candidates. It does not inspect unrequested repositories, mutate tasks, validate semantic correctness, or declare knowledge invalid. Document-level hints are deliberately coarser than claim-level reasoning; inspect the affected sections before deciding whether a current AC needs revalidation. Unmapped changes and incomplete dependency metadata are visible gaps, not proof of no impact.

```powershell
python -B -X utf8 <dlm-load-dir>/scripts/dlm_impact.py --repo-root <repo> --changed-file src/Calibration/Solver.cs --json
```

Repeat `--changed-file` or pass `--changed-files-json <repo-relative-json>` containing a UTF-8 array of paths. Deleted source paths are supported. Use `--doc-llm-root` for an explicitly selected custom root; otherwise the tool starts at `doc_llm` and honors its contract's declared root. Discovery is limited to `Domains/*/L2_Modules/*.md`. Globs are case-sensitive: `*`, `?` and `[]` match within one path component; a complete `**` component matches zero or more levels. No Git diff or external source is fetched implicitly.

JSON reports `advisory`, `does_not_change_acceptance`, changed paths, candidate paths with reasons, unmapped paths and warnings. Exit `0` means the scan completed, possibly with incomplete coverage; exit `2` means invalid input or a fatal read error. Inspect warnings, including missing dependencies. An explicitly changed, deleted L2 can still identify surviving consumers without recreating that document. None of these results assigns an AC outcome.

Run this only when a set of changed paths and a knowledge-reuse decision make the candidates useful. For a small, obvious change, follow existing L1/L2 anchors directly. Do not require a graph database, global TTL, full-tree hashes, or whole-project revalidation. A timestamp is a freshness hint; a changed dependency is a review trigger; neither alone proves a claim false.

## 3. Define a recurring decision once

For a repeated or consequential ambiguous decision, state this compact contract inline:

| Part | Meaning |
|---|---|
| Trigger | A relevant state change, repeated failure, contradiction, or completion claim |
| Evidence | Goal/AC, original observations, missing facts and material recent attempts |
| Candidates | Real, currently available actions within existing authorization, including no-match |
| Criteria | Observable inclusions/exclusions for each option; trusted rules separated from source data |
| Unknown path | Missing fact, ambiguity, stale state, unavailable tool or missing owner decision |
| Consumer and check | What the selected option changes and what observation verifies its effect |

Do not fill this for every routine action. Selection is advice, not invocation or authorization. The host checks exact paths, identities, permissions, tool availability, counts and dates; a reasoning model handles semantic interpretation. Jev or another provider is optional and requires separately authorized installation/data sharing/use. No default numeric confidence threshold or simulated probability grants permission or proves success.

Before using a delayed recommendation, check whether the relevant target, evidence, candidates or authorization changed. Refresh only affected facts and discard inapplicable advice. Independent judgments may share evidence; dependent questions wait for actual results. Preserve the existing primary Closure Review routes rather than introducing a second task-state system.

## 4. Recover from repeated failure

Respect the current request's action boundary before diagnosing. If the user explicitly asks only to recommend the next diagnostic and says not to perform it, use the supplied/allowed observations and name the unread trace, source or device check as the next action. Do not perform that proposed diagnostic merely because it is a reversible read or an earlier task allowed it. Ordinary analysis requests still permit relevant evidence reads unless the user narrows them this way.

When an equivalent attempt repeats a failure without new information, capture briefly in the existing working context: hypothesis, attempted action, observation, excluded causes, and the next check that can distinguish the remaining explanations. Inspect an unread relevant error or change the hypothesis before repeating unchanged work. Retry only when there is an evidence-based reason, such as a transient condition that changed; do not add a universal retry count.

- A locally observable fact: obtain the smallest relevant observation within scope.
- A technical uncertainty requiring exploration: use a bounded spike when justified.
- An implementation gap within the baseline: continue the current task.
- A changed goal/scope/criterion: return to the owner for the existing recalibration path.
- Missing preference/authorization or inaccessible equipment/input: identify that exact gap; more model reasoning does not supply it.
- Criteria satisfied and stop line reached: stop; optional cleanup is not recovery work.

Do not weaken original tests, reset user changes or create an automatic rollback to make a repeated error disappear. Do not repeatedly ask another judge about unchanged evidence until it agrees.

## 5. Load and resume around the next decision

Preserve required contract/manifest inputs. Then load what can change the next decision: source/evidence anchors, contrary observations, unresolved dependencies and relevant failed attempts. A relevant candidate is not proof that the available context is sufficient. If evidence is missing, follow the next source/call-chain/runtime entry rather than turning a summary into an observation. Keep raw output retrievable; preserve constraints, identifiers and errors when shortening it. Use existing source files or output locations without writing a new archive unless preservation itself is necessary and authorized.

On a real interruption or handoff, reuse the task's resume field for the goal/authorization/stop line, last applicable evidence, unresolved question, excluded routes, and next action. On return, check changes to those dependencies. Do not restart Session Init or repeat failed attempts when identity and relevant facts are stable. Use any user-supplied budget as a planning constraint, never as permission to drop decisive evidence or fabricate certainty.

## 6. Evaluate changes to this workflow

When changing these behaviors, use [behavior evaluation](../../dlm-reflect/references/behavior-evaluation.md). Code regressions verify deterministic properties; scenario execution verifies agent choices. Neither proves a production-device outcome. Narrow or remove a rule whose measured extra interruption/cost does not reduce the relevant errors; do not promote one anecdote to a global L0 rule.
