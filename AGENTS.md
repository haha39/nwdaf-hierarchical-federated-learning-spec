# Instructions for Automated Contributors

## Evidence boundaries

Keep these categories explicit and separate:

- **Authoritative 3GPP source:** normative material obtained from an official
  3GPP source. Cite the specification, exact version or release, and a locatable
  clause, table, figure, API operation, or schema path.
- **Project proposal / candidate extension:** proposed architecture, procedure,
  semantics, protocol, or schema. Never present it as existing 3GPP behavior.
- **Implementation/design evidence:** observed code, runtime behavior, test
  result, or design document. It can demonstrate feasibility or conformance but
  does not establish a 3GPP requirement.
- **Agent inference:** analysis not stated by a source. Label it as inference and
  identify the supporting evidence.

Every factual claim about a standard must have locatable specification evidence.
If the evidence is unavailable or conflicting, mark the claim unresolved.

## Scope and decisions

- Do not change the research scope or contribution boundary without human
  direction.
- Do not promote an optional or candidate design to a mandatory requirement.
- Stop and ask a human when a substantive ambiguity or evidence conflict could
  affect architecture, procedure, semantics, conformance, or contribution
  claims.

## Working modes

- **Spec Authoring:** draft or revise project proposals while preserving the
  evidence categories and confirmed scope.
- **Spec Review:** compare proposed text, protocols, or schemas with the cited
  3GPP baseline and confirmed project semantics; report findings without
  silently changing design decisions.

## Repository hygiene

- Never write private filesystem paths, credentials, internal network details,
  or content from the local normative corpus into tracked public files.
- Keep all normative sources and derived corpus content under the gitignored
  `local-specs/` directory.
- Maintain current-state documents by integrating corrections directly. Do not
  accumulate date-stamped update sections as a substitute for revision.
- Write out “hierarchical federated learning”; do not use `HFL` as shorthand.
