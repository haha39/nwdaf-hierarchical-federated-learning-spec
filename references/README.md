# 3GPP source references

This directory contains public-safe provenance and validation summaries for the
3GPP material used by this project. It does not contain the normative source
documents, converted specification text, or copies of official OpenAPI files.

The normative archives, derived Markdown corpus, extracted media, and OpenAPI
dependency closures are stored under the gitignored `local-specs/` directory.
Each source is pinned by exact version or commit identity in `manifest.yaml`.

## Scope

- 3GPP TS 23.288, Release 19 and Release 20
- 3GPP TS 29.520, Release 19 and Release 20
- The complete `TS29520_Nnwdaf_*.yaml` API set at the pinned Release 19 and
  Release 20 Forge commits
- The same-release transitive `$ref` dependency closure for each API set

Release trees are physically isolated. An unresolved same-release dependency
is a validation failure; files from another release are never used as a
fallback.

## Frozen source versions

| Release | TS 23.288 | TS 29.520 | OpenAPI identity |
| --- | --- | --- | --- |
| Release 19 | V19.7.0 | V19.7.0 | `REL-19` at `9564c5f987d8d2e37721ac2bed9ea6383a29c185` |
| Release 20 | V20.1.0 | V20.0.0 | `REL-20` at `269699e909240228d68878132c03ba87d5e871c7` |

These identities are immutable inputs to the current preparation result.
Future source refreshes must select and record new exact versions rather than
reinterpreting these entries as floating "latest" references.
