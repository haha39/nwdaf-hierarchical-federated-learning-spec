# 3GPP specification importer

This importer prepares clause-addressable local Markdown corpora for TS 23.288
and TS 29.520 and retrieves the release-isolated OpenAPI dependency closure for
the TS 29.520 NWDAF APIs.

Normative material and all derived content are written only beneath the
gitignored `local-specs/` directory. Public-safe provenance and aggregate
validation results are written beneath `references/`.

## Required tools

- Python 3.8 or later with PyYAML
- `curl`
- LibreOffice (`libreoffice` or `soffice`)
- Pandoc
- Git

## Commands

- `check-tools`: report the active conversion toolchain.
- `smoke`: convert and validate Release 19 TS 23.288 only.
- `convert`: regenerate all Markdown corpora from already downloaded archives.
- `openapi`: retrieve both pinned OpenAPI closures and run complete validation.
- `prepare`: download, convert, retrieve OpenAPI closures, and validate all inputs.
- `validate`: rerun validation without retrieving sources.

The importer never resolves an OpenAPI reference outside the selected Forge
commit and never falls back to another release tree.

Word package extraction uses Python's standard `zipfile` module. Pandoc is run
with `--from=docx --to=gfm --wrap=none`; clause files are then derived from the
recognized 3GPP heading hierarchy. Legacy `.doc` sources are first normalized
to DOCX with an isolated LibreOffice profile.
