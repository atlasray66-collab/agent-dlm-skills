# Behavior evaluation for DLM changes

Use when a DLM skill change affects loading, recovery, evidence interpretation, or stopping. This is development assurance for the changed workflow, not a required evaluation campaign for ordinary project tasks. Deterministic script tests remain the right tool for parsing, path containment, encoding, input conflicts and write failures.

## Minimal evaluation design

Choose a few cases that distinguish the changed behavior, including a valid completion where intervention would be wrong. Give the executor the realistic user request, raw task/source/evidence artifacts, the candidate skill, and exact allowed side effects. Keep expected outcomes separate from the executor's inputs. Use an isolated workspace for any authorized writes. A read-only case must stay read-only, including task status and index updates.

Where a before/after comparison is useful, keep the request, initial files, tools, authority, model settings and budgets identical and vary one workflow change. Record requested and verified model settings separately. Repeat only enough to resolve a meaningful uncertainty; a small synthetic pass does not establish production accuracy, a universal speedup, or native-host performance.

Use different task families for development and held-out checks when tuning rules. A holdout becomes a development case once its outcome informs the change. Never hide failed/aborted runs, count a queued job as execution, or give an unresolved human handoff automatic success credit. No API call, extra model, project task, or paid benchmark is implied by this reference.

## Discriminating cases

| Input condition | Observable expectation |
|---|---|
| An old leading status conflicts with explicit Meta | All task consumers use current Meta; historical text cannot override it |
| Current AC cites a passing result for another target version/environment | Result remains historical; current acceptance is unknown until applicability is established |
| Build succeeds but required visible UI/save-reload behavior was not observed | Report the build claim and missing behavior separately; select the smallest matching check |
| Optional context is missing but required evidence is sufficient | Continue authorized work; do not turn optional loading into a blocker |
| A dependency changes while unrelated evidence stays valid | Identify a bounded review candidate set, preserve unaffected evidence and historical acceptance |
| Repeated equivalent failure with no changed input | Choose new diagnostic information or a changed hypothesis, not an unchanged loop |
| User explicitly requests a next-diagnostic recommendation without executing that diagnostic | Use the allowed observations and name the unread artifact/check; do not open or run the proposed next diagnostic |
| Owner changes the route within explicit scope | Honor the latest direction, preserve applicable constraints, do not execute the superseded route |
| All accepted criteria pass and only unrelated cleanup remains | Stop at the declared line; no mandatory sediment, audit or extra task |
| Source/target changes after index preparation or replacement fails | Report conflict/failure; preserve the conflicting or original file, avoid a success claim |

Check actual actions, files, returned observations and final claims, not presence of prescribed phrases. For judgment cases, report wrong completion claims, missed constraints, unnecessary interruptions, repeated work and completed outcomes. Include elapsed time and total effort only when measured under comparable conditions. A judge agreeing with another judge is not ground truth.

## Review outcome

Retain a change when it fixes the observed error without violating the accepted scope or creating material regressions. Narrow or remove an intervention if it adds steps without useful error reduction. Failed cases should lead to the smallest rule, evidence-slice or candidate-generation repair. Preserve original failures and retest that condition and direct regressions; do not start another general audit or automatically rewrite shared/global policy.
