# Hierarchical NWDAF Federated Learning Specification

This repository supports public collaboration on a 3GPP-aware protocol and
schema proposal for hierarchical NWDAF federated learning, together with its
free5GC implementation and controlled system validation. It does not propose a
new federated learning or aggregation algorithm.

## Research scope

The current work is limited to two scenarios:

1. **Dynamic topology formation:** establish a role-neutral recursive topology
   before training, distribute topology instructions through the hierarchy,
   collect confirmations, and report the realized topology to the root.
2. **Intermediate/Branch failure recovery:** detect an unavailable intermediate
   participant, select a replacement, reparent the affected subtree, and
   continue training without rebuilding unaffected branches.

The authoritative project scope and contribution boundary are maintained by
the project owners. Candidate designs in this repository must not be treated as
existing 3GPP behavior unless supported by cited specification evidence.

## Repository structure

- `references/`: public-safe 3GPP source provenance and validation summaries.
- `tools/import_3gpp_specs/`: reproducible tooling for retrieving, converting,
  splitting, and validating the required 3GPP sources.
- `local-specs/`: local, gitignored normative sources and derived artifacts.

Future proposal and review documents may be added as the research proceeds.
The collaboration rules are defined in `AGENTS.md`, and the authoring and review
process is defined in `WORKFLOW.md`.

## Rebuilding the local 3GPP corpus

The importer pins exact TS versions and 3GPP Forge commits recorded in
`references/manifest.yaml`. It prepares clause-addressable Markdown for TS
23.288 and TS 29.520, preserves extracted assets, and retrieves the complete
`TS29520_Nnwdaf_*.yaml` set with its same-release transitive `$ref` dependency
closure.

See `tools/import_3gpp_specs/README.md` for prerequisites and commands. Generated
content is written beneath `local-specs/`, with Release 19 and Release 20 kept
physically isolated. Validation results are summarized in
`references/validation/README.md`.

## Source distribution boundary

`local-specs/` is local working data and must remain untracked. This repository
records source identity, checksums, retrieval information, conversion settings,
and validation results; it does not redistribute the complete 3GPP
specification corpus or converted normative text.
