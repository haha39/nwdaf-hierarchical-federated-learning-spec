#!/usr/bin/env python3
"""Prepare release-isolated local 3GPP corpora and public-safe provenance."""

import argparse
import datetime as dt
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
PUBLIC_MANIFEST = WORKSPACE / "references" / "manifest.yaml"
VALIDATION_README = WORKSPACE / "references" / "validation" / "README.md"
LOCAL_ROOT = WORKSPACE / "local-specs"
LOCAL_STATE = LOCAL_ROOT / "import-state.yaml"
USER_AGENT = "Mozilla/5.0 (compatible; 3GPP-source-preparation/1.0)"
CLAUSE_RE = re.compile(
    r"^(?P<clause>(?:\d+[A-Za-z]?(?:\.\d+[A-Za-z]?)*|[A-Z](?:\.\d+[A-Za-z]?)+|Annex\s+[A-Z](?:\s+\([^)]+\))?|Foreword|Contents))"
    r"(?:\s*[:.\-–—]?\s+|$)(?P<title>.*)$",
    re.IGNORECASE,
)
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tif", ".tiff"}
VECTOR_EXTENSIONS = {".emf", ".wmf"}


class ImportFailure(RuntimeError):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_timestamp_utc(path):
    timestamp = Path(path).stat().st_mtime
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_yaml(path, default=None):
    path = Path(path)
    if not path.exists():
        return {} if default is None else default
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def write_yaml(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(value, stream, sort_keys=False, allow_unicode=True, width=1000)


def write_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)


def run(command, cwd=None, env=None, capture=True, timeout=None):
    result = subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise ImportFailure("command failed ({}): {}".format(result.returncode, detail))
    return result.stdout if capture else ""


def run_bytes(command, cwd=None):
    result = subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ImportFailure(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def executable(name):
    local_candidates = [
        LOCAL_ROOT / ".toolchain" / "usr" / "bin" / name,
        LOCAL_ROOT / ".toolchain" / "bin" / name,
    ]
    for candidate in local_candidates:
        if candidate.exists() and os.access(str(candidate), os.X_OK):
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    return None


def require_tool(*names):
    for name in names:
        found = executable(name)
        if found:
            return found
    raise ImportFailure("required tool is unavailable: {}".format(" or ".join(names)))


def tool_version(command, version_args=("--version",)):
    try:
        output = run([command] + list(version_args), timeout=30)
        return output.splitlines()[0].strip() if output else "unknown"
    except Exception as exc:
        return "unavailable: {}".format(exc)


def download(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size:
        return
    curl = require_tool("curl")
    temporary = destination.with_suffix(destination.suffix + ".part")
    if temporary.exists():
        temporary.unlink()
    run(
        [
            curl,
            "-fL",
            "--retry",
            "3",
            "--retry-delay",
            "2",
            "-A",
            USER_AGENT,
            "-o",
            temporary,
            url,
        ],
        capture=False,
    )
    temporary.replace(destination)


def load_manifest():
    data = load_yaml(PUBLIC_MANIFEST)
    if not data:
        raise ImportFailure("public manifest is missing")
    return data


def load_state():
    return load_yaml(LOCAL_STATE, {"specifications": {}, "openapi": {}, "validation": {}})


def save_state(state):
    write_yaml(LOCAL_STATE, state)


def spec_key(spec_entry):
    return "Rel-{}|{}".format(spec_entry["release"], spec_entry["spec"])


def release_root(release):
    return LOCAL_ROOT / "Rel-{}".format(release)


def source_dir(release):
    return release_root(release) / "_sources"


def discover_source_document(archive, expected_stem):
    with zipfile.ZipFile(str(archive)) as package:
        candidates = [
            member
            for member in package.namelist()
            if not member.endswith("/") and Path(member).suffix.lower() in {".doc", ".docx"}
        ]
        preferred = [member for member in candidates if Path(member).stem.lower() == expected_stem.lower()]
        selected = preferred or candidates
        if len(selected) != 1:
            raise ImportFailure(
                "expected exactly one primary Word document in {}, found: {}".format(
                    archive.name, ", ".join(candidates) or "none"
                )
            )
        member = selected[0]
        data = package.read(member)
    destination = archive.parent / Path(member).name
    if not destination.exists() or sha256_bytes(data) != sha256_file(destination):
        destination.write_bytes(data)
    return destination


def normalize_to_docx(source_document, work_dir, libreoffice):
    source_document = Path(source_document)
    if source_document.suffix.lower() == ".docx":
        target = Path(work_dir) / source_document.name
        shutil.copy2(str(source_document), str(target))
        return target, False
    profile = Path(work_dir) / "libreoffice-profile"
    profile.mkdir(parents=True, exist_ok=True)
    run(
        [
            libreoffice,
            "-env:UserInstallation={}".format(profile.resolve().as_uri()),
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            work_dir,
            source_document,
        ],
        timeout=300,
    )
    target = Path(work_dir) / (source_document.stem + ".docx")
    if not target.exists():
        raise ImportFailure("LibreOffice did not produce {}".format(target.name))
    return target, True


def copy_docx_assets(docx, destination):
    original_dir = Path(destination) / "original"
    embedded_dir = Path(destination) / "embedded"
    original_dir.mkdir(parents=True, exist_ok=True)
    embedded_dir.mkdir(parents=True, exist_ok=True)
    media = []
    embedded = []
    with zipfile.ZipFile(str(docx)) as package:
        for member in package.namelist():
            if member.startswith("word/media/") and not member.endswith("/"):
                target = original_dir / Path(member).name
                target.write_bytes(package.read(member))
                media.append(target)
            elif member.startswith("word/embeddings/") and not member.endswith("/"):
                target = embedded_dir / Path(member).name
                target.write_bytes(package.read(member))
                embedded.append(target)
    return media, embedded


def make_previews(media, assets_root, libreoffice):
    rendered = Path(assets_root) / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    mapping = {}
    failures = []
    for source in media:
        suffix = source.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            target = rendered / source.name
            shutil.copy2(str(source), str(target))
            mapping[source.name] = target.relative_to(Path(assets_root).parent).as_posix()
            continue
        if suffix in VECTOR_EXTENSIONS:
            if os.environ.get("IMPORT_3GPP_VECTOR_PREVIEWS") != "1":
                failures.append(
                    {
                        "asset": source.name,
                        "reason": "vector preview not requested; original source retained",
                    }
                )
                mapping[source.name] = (Path("assets") / "original" / source.name).as_posix()
                continue
            with tempfile.TemporaryDirectory(prefix="3gpp-preview-") as profile_dir:
                profile = Path(profile_dir) / "profile"
                profile.mkdir()
                try:
                    run(
                        [
                            libreoffice,
                            "-env:UserInstallation={}".format(profile.resolve().as_uri()),
                            "--headless",
                            "--convert-to",
                            "png",
                            "--outdir",
                            rendered,
                            source,
                        ],
                        timeout=90,
                    )
                except Exception as exc:
                    failures.append({"asset": source.name, "reason": str(exc)})
            preview = rendered / (source.stem + ".png")
            if preview.exists():
                mapping[source.name] = preview.relative_to(Path(assets_root).parent).as_posix()
            else:
                if not any(item["asset"] == source.name for item in failures):
                    failures.append({"asset": source.name, "reason": "preview not produced; source retained"})
                mapping[source.name] = (Path("assets") / "original" / source.name).as_posix()
            continue
        mapping[source.name] = (Path("assets") / "original" / source.name).as_posix()
    return mapping, failures


def pandoc_convert(docx, work_dir, pandoc):
    markdown = Path(work_dir) / "converted.md"
    extracted = Path(work_dir) / "pandoc-media"
    pandoc_data = LOCAL_ROOT / ".toolchain" / "usr" / "share" / "pandoc" / "data"
    command = [pandoc]
    if pandoc_data.exists():
        command.append("--data-dir={}".format(pandoc_data))
    command.extend(
        [
            "--from=docx",
            "--to=gfm",
            "--wrap=none",
            "--extract-media={}".format(extracted),
            "--output={}".format(markdown),
            docx,
        ]
    )
    run(
        command,
        timeout=1200,
    )
    if not markdown.exists() or not markdown.stat().st_size:
        raise ImportFailure("Pandoc produced no Markdown")
    return markdown.read_text(encoding="utf-8"), extracted


def clean_heading_text(text):
    text = re.sub(r"\s+\{#[^}]+\}\s*$", "", text).strip()
    text = text.replace("\\_", "_").replace("\\#", "#")
    return text


def parse_sections(markdown):
    lines = markdown.splitlines()
    # Some 3GPP Word heading styles store the outline marker and visible clause
    # title in adjacent paragraphs. Pandoc 2.5 renders these as an empty Markdown
    # heading followed by the title. Recover that source structure explicitly.
    for index in range(len(lines) - 1):
        empty_heading = re.match(r"^(#{1,6})\s*$", lines[index])
        if not empty_heading:
            continue
        following = index + 1
        while following < len(lines) and not lines[following].strip():
            following += 1
        if following < len(lines) and CLAUSE_RE.match(clean_heading_text(lines[following].strip())):
            lines[index] = "{} {}".format(empty_heading.group(1), lines[following].strip())
            lines[following] = ""
    headings = []
    fenced = False
    for index, line in enumerate(lines):
        if line.startswith("```") or line.startswith("~~~"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = MARKDOWN_HEADING_RE.match(line)
        if not match:
            continue
        heading = clean_heading_text(match.group(2))
        clause_match = CLAUSE_RE.match(heading)
        if clause_match:
            headings.append(
                {
                    "index": index,
                    "level": len(match.group(1)),
                    "heading": heading,
                    "clause": normalize_clause(clause_match.group("clause")),
                    "title": clause_match.group("title").strip(),
                }
            )
    if not headings:
        raise ImportFailure("no clause headings were recognized")
    sections = []
    if headings[0]["index"]:
        sections.append(
            {
                "clause": "document-information",
                "title": "Document information",
                "heading": "Document information",
                "level": 1,
                "body": "\n".join(lines[: headings[0]["index"]]).strip(),
            }
        )
    for position, heading in enumerate(headings):
        end = headings[position + 1]["index"] if position + 1 < len(headings) else len(lines)
        body = "\n".join(lines[heading["index"] : end]).strip()
        section = dict(heading)
        section.pop("index")
        section["body"] = body
        sections.append(section)
    return sections


def normalize_clause(clause):
    lower = clause.lower()
    if lower == "foreword":
        return "foreword"
    if lower == "contents":
        return "contents"
    if lower.startswith("annex"):
        match = re.match(r"Annex\s+([A-Z])", clause, flags=re.IGNORECASE)
        return "Annex {}".format(match.group(1).upper()) if match else re.sub(r"\s+", " ", clause).strip()
    return clause


def clause_parent(clause):
    if clause in {"document-information", "foreword", "contents"} or clause.lower().startswith("annex"):
        return None
    if re.match(r"^[A-Z]\.\d+$", clause, flags=re.IGNORECASE):
        return "Annex {}".format(clause[0].upper())
    if "." in clause:
        return clause.rsplit(".", 1)[0]
    return None


def safe_component(value, limit=180):
    value = value.replace("/", " and ").replace("\\", " and ")
    value = re.sub(r"[\x00-\x1f:*?\"<>|]", " ", value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(".")
    if len(value) > limit:
        value = value[:limit].rstrip()
    return value or "untitled"


def section_label(section):
    clause = section["clause"]
    if clause == "document-information":
        return "00 Document information"
    if clause == "contents":
        return "01 Original contents"
    if clause == "foreword":
        return "02 Foreword"
    if clause.lower().startswith("annex"):
        return safe_component("{} {}".format(clause, section["title"]).strip())
    return safe_component("{} {}".format(clause, section["title"]).strip())


def assign_section_paths(sections):
    by_clause = {section["clause"]: section for section in sections}
    children = {section["clause"]: [] for section in sections}
    for section in sections:
        parent = clause_parent(section["clause"])
        if parent in children:
            children[parent].append(section["clause"])

    def directory_for(clause):
        parent = clause_parent(clause)
        if parent and parent in by_clause:
            parent_section = by_clause[parent]
            parent_base = directory_for(parent)
            if children[parent]:
                return parent_base / section_label(parent_section)
            return parent_base
        return Path()

    for section in sections:
        clause = section["clause"]
        base = directory_for(clause)
        if children[clause]:
            section["path"] = (base / section_label(section) / "README.md").as_posix()
            section["kind"] = "source-navigation-file"
        else:
            section["path"] = (base / (section_label(section) + ".md")).as_posix()
            section["kind"] = "source-file"
        section["children"] = children[clause]
    return sections


def yaml_quote(value):
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(spec_entry, source_archive, source_sha, source_document, document_sha, section, conversion):
    rows = [
        "---",
        "spec: {}".format(spec_entry["spec"]),
        "version: {}".format(spec_entry["version"]),
        "release: {}".format(yaml_quote(spec_entry["release"])),
        "clause: {}".format(yaml_quote(section["clause"])),
        "title: {}".format(yaml_quote(section["heading"])),
        "source_archive: {}".format(source_archive.name),
        "source_document: {}".format(source_document.name),
        "source_archive_sha256: {}".format(source_sha),
        "source_document_sha256: {}".format(document_sha),
        "content_origin: 3gpp-source",
        "conversion: {}".format(conversion),
        "---",
        "",
    ]
    return "\n".join(rows)


def rewrite_asset_links(body, output_path, asset_mapping):
    output_dir = Path(output_path).parent

    def replace(match):
        prefix = match.group(0)[: match.group(0).find("(") + 1]
        original = match.group(1)
        path_part, separator, fragment = original.partition("#")
        basename = Path(urllib.parse.unquote(path_part)).name
        if basename not in asset_mapping:
            return match.group(0)
        target = Path(asset_mapping[basename])
        relative = os.path.relpath(str(target), str(output_dir or Path("."))).replace(os.sep, "/")
        if separator:
            relative += "#" + fragment
        return prefix + relative + ")"

    return LINK_RE.sub(replace, body)


def word_count(text):
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def toc_clause_identities(sections):
    contents = next((section for section in sections if section["clause"] == "contents"), None)
    if not contents:
        return []
    identities = []
    for line in contents["body"].splitlines():
        text = re.sub(r"[*_`]", "", line).strip()
        if not re.search(r"\s\d+\s*$", text):
            continue
        text = re.sub(r"\s+\d+\s*$", "", text)
        match = CLAUSE_RE.match(text)
        if match:
            identities.append(normalize_clause(match.group("clause")))
    return list(dict.fromkeys(identities))


def convert_spec(spec_entry, state, smoke=False):
    release = str(spec_entry["release"])
    spec = spec_entry["spec"]
    archive = source_dir(release) / spec_entry["archive_filename"]
    download(spec_entry["official_source_url"], archive)
    archive_sha = sha256_file(archive)
    source_document = discover_source_document(archive, Path(spec_entry["archive_filename"]).stem)
    document_sha = sha256_file(source_document)
    destination = release_root(release) / spec
    if destination.exists():
        shutil.rmtree(str(destination))
    destination.mkdir(parents=True)

    libreoffice = require_tool("libreoffice", "soffice")
    pandoc = require_tool("pandoc")
    with tempfile.TemporaryDirectory(prefix="3gpp-convert-") as work:
        normalized_docx, normalized = normalize_to_docx(source_document, work, libreoffice)
        media, embedded = copy_docx_assets(normalized_docx, destination / "assets")
        asset_mapping, preview_failures = make_previews(media, destination / "assets", libreoffice)
        markdown, extracted = pandoc_convert(normalized_docx, work, pandoc)
        for extracted_file in extracted.rglob("*") if extracted.exists() else []:
            if extracted_file.is_file() and extracted_file.name not in asset_mapping:
                target = destination / "assets" / "original" / extracted_file.name
                shutil.copy2(str(extracted_file), str(target))
                media.append(target)
                asset_mapping[target.name] = (Path("assets") / "original" / target.name).as_posix()

    raw_note_count = len(re.findall(r"\bNOTE(?:\s+\d+)?\s*:", markdown, flags=re.IGNORECASE))
    raw_table_rows = sum(1 for line in markdown.splitlines() if line.strip().startswith("|") and line.strip().endswith("|"))
    raw_html_tables = len(re.findall(r"<table(?:\s|>)", markdown, flags=re.IGNORECASE))
    raw_html_rows = len(re.findall(r"<tr(?:\s|>)", markdown, flags=re.IGNORECASE))
    sections = assign_section_paths(parse_sections(markdown))
    toc_clauses = toc_clause_identities(sections)
    section_clauses = {section["clause"] for section in sections}
    toc_missing = [clause for clause in toc_clauses if clause not in section_clauses]
    section_index = {section["clause"]: section for section in sections}
    conversion_name = "libreoffice-doc-to-docx+pandoc-gfm-clause-split" if normalized else "pandoc-gfm-clause-split"
    written_bodies = []
    manifest_sections = []
    for section in sections:
        body = rewrite_asset_links(section["body"], section["path"], asset_mapping)
        if section["children"]:
            nav = ["", "## Child clauses", ""]
            current_dir = Path(section["path"]).parent
            for child_clause in section["children"]:
                child = section_index[child_clause]
                relative = os.path.relpath(child["path"], str(current_dir)).replace(os.sep, "/")
                nav.append("- [{}]({})".format(child["heading"], urllib.parse.quote(relative, safe="/._-")))
            body += "\n" + "\n".join(nav)
        output = destination / section["path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        write_text(
            output,
            frontmatter(
                spec_entry,
                archive,
                archive_sha,
                source_document,
                document_sha,
                section,
                conversion_name,
            )
            + body.strip()
            + "\n",
        )
        written_bodies.append(body)
        manifest_sections.append(
            {
                "clause": section["clause"],
                "title": section["heading"],
                "path": section["path"],
                "source_words": word_count(section["body"]),
                "kind": section["kind"],
            }
        )

    root_lines = [
        "# {} V{} (Release {})".format(spec, spec_entry["version"], release),
        "",
        "This local corpus is derived from the pinned authoritative 3GPP source archive.",
        "It is excluded from version control.",
        "",
        "## Clauses",
        "",
    ]
    for section in sections:
        if clause_parent(section["clause"]) is None:
            root_lines.append(
                "- [{}]({})".format(section["heading"], urllib.parse.quote(section["path"], safe="/._-"))
            )
    write_text(destination / "README.md", "\n".join(root_lines) + "\n")

    converted_text = "\n".join(written_bodies)
    converted_note_count = len(re.findall(r"\bNOTE(?:\s+\d+)?\s*:", converted_text, flags=re.IGNORECASE))
    converted_table_rows = sum(
        1 for line in converted_text.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")
    )
    converted_html_tables = len(re.findall(r"<table(?:\s|>)", converted_text, flags=re.IGNORECASE))
    converted_html_rows = len(re.findall(r"<tr(?:\s|>)", converted_text, flags=re.IGNORECASE))
    local_manifest = {
        "spec": spec,
        "version": spec_entry["version"],
        "release": release,
        "source_archive": archive.name,
        "official_source_url": spec_entry["official_source_url"],
        "source_archive_sha256": archive_sha,
        "source_document": source_document.name,
        "source_document_sha256": document_sha,
        "retrieved_at": file_timestamp_utc(archive),
        "conversion": {
            "method": conversion_name,
            "pandoc": tool_version(pandoc),
            "libreoffice": tool_version(libreoffice, ("--headless", "--version")),
            "normalized_legacy_doc": normalized,
            "settings": {
                "pandoc_from": "docx",
                "pandoc_to": "gfm",
                "wrap": "none",
                "media_extraction": "docx-package-and-pandoc",
                "split_policy": "recognized-3gpp-clause-hierarchy",
                "vector_preview_policy": "optional-source-retained",
            },
        },
        "sections": manifest_sections,
        "assets": {
            "original_media": len(media),
            "embedded_objects": len(embedded),
            "preview_failures": preview_failures,
        },
        "conversion_counts": {
            "source_note_markers": raw_note_count,
            "converted_note_markers": converted_note_count,
            "source_markdown_table_rows": raw_table_rows,
            "converted_markdown_table_rows": converted_table_rows,
            "source_html_tables": raw_html_tables,
            "converted_html_tables": converted_html_tables,
            "source_html_table_rows": raw_html_rows,
            "converted_html_table_rows": converted_html_rows,
            "toc_clause_count": len(toc_clauses),
            "toc_clauses_missing_from_split": toc_missing,
        },
    }
    write_yaml(destination / "manifest.yaml", local_manifest)
    state["specifications"][spec_key(spec_entry)] = local_manifest
    save_state(state)
    return local_manifest


def iter_refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value
            else:
                yield from iter_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_refs(value)


def keyword_counts(node, counts=None):
    if counts is None:
        counts = {key: 0 for key in ("required", "enum", "oneOf", "allOf", "anyOf")}
    if isinstance(node, dict):
        for key, value in node.items():
            if key in counts:
                counts[key] += 1
            keyword_counts(value, counts)
    elif isinstance(node, list):
        for value in node:
            keyword_counts(value, counts)
    return counts


def resolve_repo_ref(current_path, ref):
    parsed = urllib.parse.urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        raise ImportFailure("external URL $ref is outside the pinned Forge commit: {}".format(ref))
    if not parsed.path:
        return current_path, urllib.parse.unquote(parsed.fragment)
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(current_path), urllib.parse.unquote(parsed.path)))
    if joined == ".." or joined.startswith("../") or joined.startswith("/"):
        raise ImportFailure("$ref escapes the release repository root: {}".format(ref))
    return joined, urllib.parse.unquote(parsed.fragment)


def git_show(repo, commit, path):
    return run_bytes(["git", "show", "{}:{}".format(commit, path)], cwd=repo)


def validate_json_pointer(document, fragment, ref_label):
    if not fragment:
        return
    if not fragment.startswith("/"):
        raise ImportFailure("unsupported non-JSON-pointer fragment in {}".format(ref_label))
    current = document
    for raw in fragment.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ImportFailure("unresolved JSON pointer in {} at {}".format(ref_label, token))


def import_openapi(openapi_entry, state):
    release = str(openapi_entry["release"])
    commit = openapi_entry["commit"]
    repository = openapi_entry["forge_repository"]
    destination = release_root(release) / "openapi"
    if destination.exists():
        shutil.rmtree(str(destination))
    destination.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="3gpp-forge-") as temporary:
        repo = Path(temporary) / "repo"
        repo.mkdir()
        run(["git", "init", "--quiet"], cwd=repo)
        run(["git", "remote", "add", "origin", repository], cwd=repo)
        # Git 2.25 requires the partial-clone repository extension to be set
        # explicitly when a repository was created with `git init`.
        run(["git", "config", "extensions.partialClone", "origin"], cwd=repo)
        run(["git", "config", "remote.origin.promisor", "true"], cwd=repo)
        run(["git", "config", "remote.origin.partialclonefilter", "blob:none"], cwd=repo)
        run(
            [
                "git",
                "-c",
                "protocol.version=2",
                "fetch",
                "--quiet",
                "--depth=1",
                "--filter=blob:none",
                "origin",
                commit,
            ],
            cwd=repo,
            timeout=1200,
        )
        fetched = run(["git", "rev-parse", "FETCH_HEAD"], cwd=repo).strip()
        if fetched != commit:
            raise ImportFailure("Forge fetch identity mismatch: expected {}, got {}".format(commit, fetched))
        tree_paths = set(run(["git", "ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines())
        initial = sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).name.startswith("TS29520_Nnwdaf_") and path.lower().endswith((".yaml", ".yml"))
        )
        if not initial:
            raise ImportFailure("no TS29520_Nnwdaf_*.yaml files found at {}".format(commit))
        queue = list(initial)
        documents = {}
        raw_files = {}
        refs_by_file = {}
        while queue:
            repo_path = queue.pop(0)
            if repo_path in documents:
                continue
            if repo_path not in tree_paths:
                raise ImportFailure("same-release dependency is absent at {}: {}".format(commit, repo_path))
            raw = git_show(repo, commit, repo_path)
            try:
                document = yaml.safe_load(raw.decode("utf-8-sig"))
            except Exception as exc:
                raise ImportFailure("YAML parse failure in {}: {}".format(repo_path, exc))
            documents[repo_path] = document
            raw_files[repo_path] = raw
            references = list(iter_refs(document))
            refs_by_file[repo_path] = references
            for reference in references:
                dependency, _ = resolve_repo_ref(repo_path, reference)
                if dependency not in documents and dependency not in queue:
                    queue.append(dependency)

        for repo_path, raw in raw_files.items():
            output = destination / repo_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(raw)

    for repo_path, references in refs_by_file.items():
        for reference in references:
            dependency, fragment = resolve_repo_ref(repo_path, reference)
            if dependency not in documents:
                raise ImportFailure("dependency closure is incomplete: {} -> {}".format(repo_path, reference))
            validate_json_pointer(documents[dependency], fragment, "{} -> {}".format(repo_path, reference))

    file_records = []
    initial_set = set(initial)
    aggregate_keywords = {key: 0 for key in ("required", "enum", "oneOf", "allOf", "anyOf")}
    for repo_path in sorted(documents):
        document = documents[repo_path]
        counts = keyword_counts(document)
        for key, value in counts.items():
            aggregate_keywords[key] += value
        info = document.get("info", {}) if isinstance(document, dict) else {}
        file_records.append(
            {
                "file": repo_path,
                "role": "ts-29.520-api" if repo_path in initial_set else "dependency",
                "sha256": sha256_bytes(raw_files[repo_path]),
                "info_title": info.get("title", ""),
                "info_version": str(info.get("version", "")),
                "external_ref_count": sum(1 for ref in refs_by_file[repo_path] if urllib.parse.urlsplit(ref).path),
            }
        )
    local_manifest = {
        "release": release,
        "branch": openapi_entry["branch"],
        "commit": commit,
        "forge_repository": repository,
        "retrieved_at": utc_now(),
        "isolation_policy": "same-release-only-no-fallback",
        "api_file_count": len(initial),
        "dependency_file_count": len(documents) - len(initial),
        "files": file_records,
        "validation": {
            "yaml_parse": "PASS",
            "ref_resolution": "PASS",
            "release_isolation": "PASS",
            "schema_keyword_counts": aggregate_keywords,
        },
    }
    write_yaml(destination / "manifest.yaml", local_manifest)
    readme = [
        "# TS 29.520 OpenAPI dependency closure — Release {}".format(release),
        "",
        "Forge commit: `{}`".format(commit),
        "",
        "This directory contains the complete TS 29.520 NWDAF API set and its same-release",
        "transitive `$ref` dependency closure. It is excluded from version control.",
        "",
        "## TS 29.520 API files",
        "",
    ]
    for record in file_records:
        if record["role"] == "ts-29.520-api":
            readme.append("- `{}` — API {}".format(record["file"], record["info_version"] or "unversioned"))
    readme.extend(["", "## Dependency files", ""])
    for record in file_records:
        if record["role"] == "dependency":
            readme.append("- `{}`".format(record["file"]))
    write_text(destination / "README.md", "\n".join(readme) + "\n")
    state["openapi"]["Rel-{}".format(release)] = local_manifest
    save_state(state)
    return local_manifest


def validate_links(spec_root, manifest):
    failures = []
    checked = 0
    for section in manifest["sections"]:
        path = spec_root / section["path"]
        if not path.exists():
            failures.append("missing section: {}".format(section["path"]))
            continue
        text = path.read_text(encoding="utf-8")
        expected_clause = 'clause: "{}"'.format(section["clause"])
        if expected_clause not in text:
            failures.append("clause identity missing from {}".format(section["path"]))
        for match in LINK_RE.finditer(text):
            raw = match.group(1).split("#", 1)[0]
            if not raw or urllib.parse.urlsplit(raw).scheme:
                continue
            checked += 1
            target = (path.parent / urllib.parse.unquote(raw)).resolve()
            try:
                target.relative_to(spec_root.resolve())
            except ValueError:
                failures.append("link escapes spec root: {} -> {}".format(section["path"], raw))
                continue
            if not target.exists():
                failures.append("broken local link: {} -> {}".format(section["path"], raw))
    return checked, failures


def validate_spec(spec_entry, local_manifest):
    release = str(spec_entry["release"])
    root = release_root(release) / spec_entry["spec"]
    archive = source_dir(release) / spec_entry["archive_filename"]
    failures = []
    warnings = []
    if not archive.exists() or sha256_file(archive) != local_manifest["source_archive_sha256"]:
        failures.append("source archive checksum mismatch")
    document = source_dir(release) / local_manifest["source_document"]
    if not document.exists() or sha256_file(document) != local_manifest["source_document_sha256"]:
        failures.append("source document missing or checksum mismatch")
    clauses = [row["clause"] for row in local_manifest["sections"]]
    if len(clauses) != len(set(clauses)):
        failures.append("duplicate clause identities")
    numeric_top = sorted(int(value) for value in clauses if value.isdigit())
    if numeric_top:
        expected = list(range(1, max(numeric_top) + 1))
        if numeric_top != expected:
            failures.append("top-level clause sequence is discontinuous: {}".format(numeric_top))
    link_count, link_failures = validate_links(root, local_manifest)
    failures.extend(link_failures)
    counts = local_manifest["conversion_counts"]
    if counts["source_note_markers"] != counts["converted_note_markers"]:
        failures.append("NOTE marker count changed during clause splitting")
    if counts["source_markdown_table_rows"] != counts["converted_markdown_table_rows"]:
        failures.append("Markdown table row count changed during clause splitting")
    if counts["source_html_tables"] != counts["converted_html_tables"]:
        failures.append("HTML table count changed during clause splitting")
    if counts["source_html_table_rows"] != counts["converted_html_table_rows"]:
        failures.append("HTML table row count changed during clause splitting")
    if counts["toc_clauses_missing_from_split"]:
        failures.append(
            "TOC clause identities missing from split corpus: {}".format(
                ", ".join(counts["toc_clauses_missing_from_split"][:20])
            )
        )
    preview_failures = local_manifest["assets"]["preview_failures"]
    if preview_failures:
        warnings.append("{} media previews were not produced; original assets were retained".format(len(preview_failures)))
    return {
        "status": "PASS" if not failures else "FAIL",
        "archive_checksum": "PASS" if not any("archive checksum" in item for item in failures) else "FAIL",
        "source_document": "PASS" if not any("source document" in item for item in failures) else "FAIL",
        "clause_count": len(clauses),
        "navigation_links_checked": link_count,
        "note_markers": counts["converted_note_markers"],
        "markdown_table_rows": counts["converted_markdown_table_rows"],
        "html_tables": counts["converted_html_tables"],
        "toc_clause_count": counts["toc_clause_count"],
        "failures": failures,
        "warnings": warnings,
    }


def validate_openapi_local(openapi_entry, local_manifest):
    release = str(openapi_entry["release"])
    root = release_root(release) / "openapi"
    failures = []
    documents = {}
    expected_paths = {record["file"] for record in local_manifest["files"]}
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"} and path.name != "manifest.yaml"
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        failures.append("OpenAPI file-set mismatch; missing={}, extra={}".format(missing, extra))
    for record in local_manifest["files"]:
        relative = record["file"]
        path = root / relative
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            failures.append("recorded file escapes release root: {}".format(relative))
            continue
        if not path.exists():
            continue
        if sha256_file(path) != record["sha256"]:
            failures.append("checksum mismatch: {}".format(relative))
        try:
            documents[relative] = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            failures.append("YAML parse failure in {}: {}".format(relative, exc))
    aggregate_keywords = {key: 0 for key in ("required", "enum", "oneOf", "allOf", "anyOf")}
    for relative, document in documents.items():
        counts = keyword_counts(document)
        for key, value in counts.items():
            aggregate_keywords[key] += value
        for reference in iter_refs(document):
            try:
                dependency, fragment = resolve_repo_ref(relative, reference)
                if dependency not in documents:
                    failures.append("unresolved same-release dependency: {} -> {}".format(relative, reference))
                    continue
                validate_json_pointer(documents[dependency], fragment, "{} -> {}".format(relative, reference))
            except ImportFailure as exc:
                failures.append(str(exc))
    expected_keywords = local_manifest["validation"]["schema_keyword_counts"]
    if aggregate_keywords != expected_keywords:
        failures.append("schema keyword counts changed")
    api_count = sum(1 for record in local_manifest["files"] if record["role"] == "ts-29.520-api")
    dependency_count = sum(1 for record in local_manifest["files"] if record["role"] == "dependency")
    return {
        "status": "PASS" if not failures else "FAIL",
        "api_file_count": api_count,
        "dependency_file_count": dependency_count,
        "schema_keyword_counts": aggregate_keywords,
        "failures": failures,
    }


def validate_all(manifest, state):
    results = {"specifications": {}, "openapi": {}, "release_isolation": "PASS"}
    for entry in manifest["specifications"]:
        key = spec_key(entry)
        local = state["specifications"].get(key)
        if not local:
            results["specifications"][key] = {"status": "NOT_RUN", "failures": ["not imported"]}
            continue
        results["specifications"][key] = validate_spec(entry, local)
    for entry in manifest["openapi"]:
        key = "Rel-{}".format(entry["release"])
        local = state["openapi"].get(key)
        if not local:
            results["openapi"][key] = {"status": "NOT_RUN"}
        else:
            results["openapi"][key] = validate_openapi_local(entry, local)
    statuses = [row["status"] for group in (results["specifications"], results["openapi"]) for row in group.values()]
    results["status"] = "PASS" if statuses and all(status == "PASS" for status in statuses) else "PARTIAL_OR_FAIL"
    results["validated_at"] = utc_now()
    state["validation"] = results
    save_state(state)
    update_public_outputs(manifest, state)
    return results


def update_public_outputs(manifest, state):
    completed_specs = []
    for entry in manifest["specifications"]:
        public = dict(entry)
        local = state["specifications"].get(spec_key(entry))
        result = state.get("validation", {}).get("specifications", {}).get(spec_key(entry))
        if local:
            public.update(
                {
                    "archive_sha256": local["source_archive_sha256"],
                    "source_document": local["source_document"],
                    "source_document_sha256": local["source_document_sha256"],
                    "retrieved_at": local["retrieved_at"],
                    "conversion": local["conversion"],
                    "validation": result["status"] if result else "pending",
                }
            )
        completed_specs.append(public)
    completed_openapi = []
    for entry in manifest["openapi"]:
        public = dict(entry)
        key = "Rel-{}".format(entry["release"])
        local = state["openapi"].get(key)
        result = state.get("validation", {}).get("openapi", {}).get(key)
        if local:
            api_files = []
            dependency_files = []
            for record in local["files"]:
                public_record = {
                    "file": record["file"],
                    "sha256": record["sha256"],
                    "info_version": record["info_version"],
                }
                if record["role"] == "ts-29.520-api":
                    api_files.append(public_record)
                else:
                    dependency_files.append(public_record)
            public.update(
                {
                    "retrieved_at": local["retrieved_at"],
                    "api_files": api_files,
                    "dependency_files": dependency_files,
                    "validation": result["status"] if result else "pending",
                }
            )
        completed_openapi.append(public)
    result = state.get("validation", {})
    manifest["specifications"] = completed_specs
    manifest["openapi"] = completed_openapi
    manifest["status"] = result.get("status", "pending")
    pandoc_packages = []
    package_dir = LOCAL_ROOT / ".toolchain" / "packages"
    for package in sorted(package_dir.glob("pandoc*.deb")) if package_dir.exists() else []:
        pandoc_packages.append({"file": package.name, "sha256": sha256_file(package)})
    manifest["toolchain"] = {
        "python": sys.version.split()[0],
        "pyyaml": yaml.__version__,
        "pandoc": tool_version(require_tool("pandoc")),
        "pandoc_local_packages": pandoc_packages,
        "libreoffice": tool_version(require_tool("libreoffice", "soffice"), ("--headless", "--version")),
        "git": tool_version(require_tool("git")),
        "curl": tool_version(require_tool("curl")),
    }
    manifest["validation"] = {
        "status": result.get("status", "pending"),
        "validated_at": result.get("validated_at", "pending"),
        "summary": "references/validation/README.md",
    }
    write_yaml(PUBLIC_MANIFEST, manifest)
    write_validation_readme(state)


def write_validation_readme(state):
    result = state.get("validation", {})
    lines = [
        "# Source preparation validation",
        "",
        "Status: **{}**".format(result.get("status", "pending")),
        "",
        "Validated at: `{}`".format(result.get("validated_at", "pending")),
        "",
        "This report contains aggregate validation results only. Normative source text,",
        "converted Markdown, and OpenAPI bodies remain under the gitignored `local-specs/` tree.",
        "",
        "## Specification conversion",
        "",
        "| Release and specification | Status | Clauses | Links checked | NOTE markers | Table rows |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for key, row in result.get("specifications", {}).items():
        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                key.replace("|", " / "),
                row.get("status", "NOT_RUN"),
                row.get("clause_count", 0),
                row.get("navigation_links_checked", 0),
                row.get("note_markers", 0),
                row.get("markdown_table_rows", 0),
            )
        )
    lines.extend(
        [
            "",
            "The conversion checks source archive and document checksums, top-level clause",
            "continuity, unique clause identities, local navigation and media targets, and",
            "NOTE/table-marker preservation across clause splitting.",
            "",
            "## OpenAPI closure",
            "",
            "| Release | Status | TS 29.520 APIs | Dependency files |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for key, row in result.get("openapi", {}).items():
        lines.append(
            "| {} | {} | {} | {} |".format(
                key,
                row.get("status", "NOT_RUN"),
                row.get("api_file_count", 0),
                row.get("dependency_file_count", 0),
            )
        )
    lines.extend(
        [
            "",
            "Each YAML file is parsed from its byte-preserved Forge representation. Every",
            "external `$ref` and JSON Pointer fragment is resolved within the same pinned",
            "release commit. Schema keyword counts are recorded for `required`, `enum`,",
            "`oneOf`, `allOf`, and `anyOf`.",
            "",
            "## Findings",
            "",
        ]
    )
    findings = []
    for key, row in result.get("specifications", {}).items():
        for failure in row.get("failures", []):
            findings.append("- **{}:** {}".format(key, failure))
        for warning in row.get("warnings", []):
            findings.append("- **{} warning:** {}".format(key, warning))
    for key, row in result.get("openapi", {}).items():
        for failure in row.get("failures", []):
            findings.append("- **{} OpenAPI:** {}".format(key, failure))
    if not findings:
        findings.append("- No validation failures or warnings.")
    lines.extend(findings)
    write_text(VALIDATION_README, "\n".join(lines) + "\n")


def write_release_readmes(manifest):
    for release in ("19", "20"):
        root = release_root(release)
        root.mkdir(parents=True, exist_ok=True)
        lines = [
            "# 3GPP Release {} local source corpus".format(release),
            "",
            "This directory is excluded from version control.",
            "",
        ]
        for entry in manifest["specifications"]:
            if str(entry["release"]) == release:
                lines.append("- [{} V{}]({}/README.md)".format(entry["spec"], entry["version"], urllib.parse.quote(entry["spec"])))
        lines.append("- [TS 29.520 OpenAPI dependency closure](openapi/README.md)")
        write_text(root / "README.md", "\n".join(lines) + "\n")


def ensure_gitignore():
    gitignore = WORKSPACE / ".gitignore"
    content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if not any(line.strip().rstrip("/") == "local-specs" for line in content.splitlines()):
        raise ImportFailure(".gitignore does not exclude local-specs/")


def cmd_smoke():
    ensure_gitignore()
    manifest = load_manifest()
    state = load_state()
    entry = next(row for row in manifest["specifications"] if row["spec"] == "TS 23.288" and str(row["release"]) == "19")
    result = convert_spec(entry, state, smoke=True)
    validation = validate_spec(entry, result)
    state["validation"] = {
        "status": "SMOKE_PASS" if validation["status"] == "PASS" else "SMOKE_FAIL",
        "validated_at": utc_now(),
        "specifications": {spec_key(entry): validation},
        "openapi": {},
        "release_isolation": "NOT_RUN",
    }
    save_state(state)
    if validation["status"] != "PASS":
        raise ImportFailure("smoke validation failed: {}".format("; ".join(validation["failures"])))
    print(yaml.safe_dump(validation, sort_keys=False))


def cmd_prepare():
    ensure_gitignore()
    manifest = load_manifest()
    state = load_state()
    for entry in manifest["specifications"]:
        print("Converting {} Release {} V{}".format(entry["spec"], entry["release"], entry["version"]), flush=True)
        convert_spec(entry, state)
    for entry in manifest["openapi"]:
        print("Retrieving OpenAPI Release {} at {}".format(entry["release"], entry["commit"]), flush=True)
        import_openapi(entry, state)
    write_release_readmes(manifest)
    results = validate_all(manifest, state)
    print(yaml.safe_dump(results, sort_keys=False))
    if results["status"] != "PASS":
        raise ImportFailure("full validation did not pass")


def cmd_openapi():
    ensure_gitignore()
    manifest = load_manifest()
    state = load_state()
    for entry in manifest["openapi"]:
        print("Retrieving OpenAPI Release {} at {}".format(entry["release"], entry["commit"]), flush=True)
        import_openapi(entry, state)
    write_release_readmes(manifest)
    results = validate_all(manifest, state)
    print(yaml.safe_dump(results, sort_keys=False))
    if results["status"] != "PASS":
        raise ImportFailure("full validation did not pass")


def cmd_convert():
    ensure_gitignore()
    manifest = load_manifest()
    state = load_state()
    for entry in manifest["specifications"]:
        print("Converting {} Release {} V{}".format(entry["spec"], entry["release"], entry["version"]), flush=True)
        convert_spec(entry, state)
    write_release_readmes(manifest)
    results = validate_all(manifest, state)
    print(yaml.safe_dump(results, sort_keys=False))
    if results["status"] != "PASS":
        raise ImportFailure("full validation did not pass")


def cmd_validate():
    manifest = load_manifest()
    state = load_state()
    results = validate_all(manifest, state)
    print(yaml.safe_dump(results, sort_keys=False))
    if results["status"] != "PASS":
        raise ImportFailure("validation did not pass")


def cmd_tools():
    rows = {
        "python": sys.version.split()[0],
        "pyyaml": yaml.__version__,
        "curl": tool_version(require_tool("curl")),
        "git": tool_version(require_tool("git")),
        "libreoffice": tool_version(require_tool("libreoffice", "soffice"), ("--headless", "--version")),
        "pandoc": tool_version(require_tool("pandoc")),
    }
    print(yaml.safe_dump(rows, sort_keys=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check-tools", "smoke", "prepare", "convert", "openapi", "validate"))
    args = parser.parse_args()
    try:
        if args.command == "check-tools":
            cmd_tools()
        elif args.command == "smoke":
            cmd_smoke()
        elif args.command == "prepare":
            cmd_prepare()
        elif args.command == "openapi":
            cmd_openapi()
        elif args.command == "convert":
            cmd_convert()
        elif args.command == "validate":
            cmd_validate()
    except ImportFailure as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
