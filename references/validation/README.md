# Source preparation validation

Status: **PASS**

Validated at: `2026-09-05T10:12:52Z`

This report contains aggregate validation results only. Normative source text,
converted Markdown, and OpenAPI bodies remain under the gitignored `local-specs/` tree.

## Specification conversion

| Release and specification | Status | Clauses | Links checked | NOTE markers | Table rows |
| --- | --- | ---: | ---: | ---: | ---: |
| Rel-19 / TS 23.288 | PASS | 482 | 462 | 615 | 1427 |
| Rel-19 / TS 29.520 | PASS | 918 | 918 | 483 | 2670 |
| Rel-20 / TS 23.288 | PASS | 494 | 474 | 639 | 712 |
| Rel-20 / TS 29.520 | PASS | 927 | 927 | 513 | 2747 |

The conversion checks source archive and document checksums, top-level clause
continuity, unique clause identities, local navigation and media targets, and
NOTE/table-marker preservation across clause splitting.

## OpenAPI closure

| Release | Status | TS 29.520 APIs | Dependency files |
| --- | --- | ---: | ---: |
| Rel-19 | PASS | 10 | 109 |
| Rel-20 | PASS | 10 | 114 |

Each YAML file is parsed from its byte-preserved Forge representation. Every
external `$ref` and JSON Pointer fragment is resolved within the same pinned
release commit. Schema keyword counts are recorded for `required`, `enum`,
`oneOf`, `allOf`, and `anyOf`.

## Findings

- **Rel-19|TS 23.288 warning:** 106 media previews were not produced; original assets were retained
- **Rel-19|TS 29.520 warning:** 69 media previews were not produced; original assets were retained
- **Rel-20|TS 23.288 warning:** 109 media previews were not produced; original assets were retained
- **Rel-20|TS 29.520 warning:** 71 media previews were not produced; original assets were retained
