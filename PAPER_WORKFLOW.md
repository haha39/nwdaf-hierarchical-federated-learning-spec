# Paper Writing Workflow

## Purpose

This workflow governs manuscript drafting and review after completion of the
specification phase. It does not redefine the research scope, Stage 2
semantics, Stage 3 realization, implementation state, or experimental evidence.
The existing specification workflow remains authoritative for specification
work.

## Authority and Source Map

For Chapter III, use the following authority order and portable source
locators:

1. **Scope, contribution, and paper-claim authority:** the current
   Human-provided Scope / Contribution Freeze. Its locator is supplied through
   the current session or private project context and must not be copied into
   tracked public files.
2. **Stage 2 semantic authority:** repository
   `haha39/nwdaf-hierarchical-federated-learning-spec`,
   `spec/stage2/hierarchical-federated-learning-stage2.md`.
3. **Stage 3 protocol and schema realization:** repository
   `ChingJe/nwdaf-docs`,
   `docs/design/hierarchical-federated-learning/candidate_openapi_schema.md`;
   consult `docs/design/hierarchical-federated-learning/candidate_openapi.yaml`
   only when machine-readable schema detail is necessary.
4. **Implementation evidence:** current implementation code and commit when
   available, supported as applicable by `ChingJe/nwdaf-docs` and
   `ChingJe/testbed-docs`. Worklogs may help locate evidence but do not by
   themselves prove an implementation claim.
5. **Experiment evidence:** actual run configuration, logs, metrics, and result
   artifacts. A worklog statement such as "complete" or "passed" is not by
   itself empirical evidence.

The latest Human-provided ChatGPT Session Handoff may be used as session and
bootstrap context, but it is not research-scope authority. Its private locator
must remain outside tracked public files.

Do not hard-code transient commit SHAs in this source map unless a specific
task requires one. Current repository state and the current Human instruction
determine transient state.

## Paper Drafting

Paper Drafting is write-capable within the Human-approved task and follows
these principles:

- **Source-bounded drafting:** Write only from the sources designated for the
  subsection or task. Do not silently fill unsupported gaps.
- **Scope-bounded writing:** Do not expand the manuscript merely for
  completeness. Stage 3 capabilities do not automatically belong in the paper.
- **Claim discipline:** Keep designed or specified, implemented, and
  experimentally validated claims distinct. Do not infer implementation from
  Stage 2 or Stage 3, or validation from implementation.
- **Manuscript-style discipline:** Write as a systems or research paper, not as
  a 3GPP specification, design document, or OpenAPI manual. Preserve technical
  precision while explaining why the mechanism exists and how it works. Avoid
  excessive defensive wording, unnecessary hedging, generic AI prose,
  repeated transitions, and unsupported adjectives.
- **Revision discipline:** Prefer revise, replace, merge, or delete over
  append-first writing. Maintain one current version of a subsection instead
  of accumulating "updated," "additional," or date-stamped addenda. Do not
  invent terminology or abbreviations when confirmed terminology exists.
- **Session discipline:** Bound each drafting session to one subsection or
  coherent revision task. When context becomes noisy, repetitive, or dominated
  by obsolete discussion, start a fresh session with only the required sources
  and task-specific context.

## Paper Review

Paper Review is strictly read-only. It must not modify manuscript,
specification, workflow, or source files, or any repository state. It may report
findings, explain risks, propose wording, or provide patch-style suggestions in
its response. Only the Human or Paper Drafting may apply changes.

Review checks include:

- technical fidelity to authoritative sources;
- source support and claim strength;
- boundaries between designed, implemented, and validated claims;
- scope creep and terminology consistency;
- logical flow and redundancy;
- prose that reads too much like a specification or API reference;
- generic or repetitive AI-writing patterns; and
- unnecessary defensive wording.

Review before rewrite: first report findings and distinguish material issues
from stylistic preferences. Do not silently redesign the system while
reviewing. Return substantive disagreements to the Human for decision.

Paper Drafting and Paper Review should normally use separate agent or session
contexts for subsection-level review. The reviewer evaluates the current draft
against authoritative sources rather than relying on the drafting agent's
rationale.

## Human Gate

The Human remains responsible for research scope, contribution and claim
boundaries, substantive technical interpretation, acceptance or rejection of
reviewer findings, and final manuscript wording and integration.

## Public-Safe / Local Workspace Boundary

Never copy or publish local filesystem paths, private workspace locations,
credentials, internal URLs, private testbed details, or other local-only
information into tracked repository files. Use portable repository names and
repository-relative paths in tracked documentation.

Local manuscript drafts, translations, scratch notes, and temporary review
artifacts may remain outside tracked repository state. English manuscript text
is canonical; translations are reading aids unless the Human explicitly states
otherwise.
