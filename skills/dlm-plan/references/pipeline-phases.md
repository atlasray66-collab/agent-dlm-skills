# DLM Plan 7 Pipeline

## 1. Scope Evidence

Perform one combined repository/authority/safety lock, then map requirement terms to real source, tests, Domains and L2 routes. Record facts, inferences, exclusions and unresolved decisions separately. Do not repeat control-plane preflight when identity and authority remain stable.

## 2. Design

Describe current state, intended target state, decisions, alternatives, failure modes, rollback or field boundary, and claim-matched verification. For execution-ready work, create a Draft Acceptance Baseline with Authorized Scope, criteria, evidence, owner, and stop line; freeze it once before substantive execution or external mutation. A user-approved implementation request authorizes ordinary task scaffolding but not new external authority; pause only for a material unresolved choice, L0/BRIEF change, external import, irreversible action, or true Baseline invalidation.

## 3. Decomposition

Each Subtask owns one verifiable outcome and states its causal contribution, material risk, evidence class, and stopping condition. Dependencies form an acyclic graph. Priority communicates urgency/risk and does not encode topology. Use project-declared statuses; DLM 7 projects support pending, in-progress, blocked, cancelled and completed. Administrative-only work is nonblocking unless a real consumer or accepted contract requires it.

## 4. Context Protocol

Generate schema-2 manifests with the current `project_id`. Paths are repository-relative files using `/`. Required entries must exist; optional deferred entries are loaded only when needed. Choose context by semantics rather than fixed file-count thresholds.

## 5. Scaffolding and Validation

Create only project-local Task artifacts that the requested outcome or a real consumer needs, synchronize compiled indexes once after the target stabilizes, run relevant project/contract validation, and inspect the final diff. A nonzero result blocks materialization only when it violates the Frozen/current baseline, applicable DLM contract, touched artifact integrity, or a demonstrated material safety boundary. Unrelated pre-existing and administrative failures are reported without becoming new completion criteria; green tooling proves only the claim it measures.
