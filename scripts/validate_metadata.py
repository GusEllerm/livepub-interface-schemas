#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_TITLE = "LivePublication Interface Schemas"
EXPECTED_ORCID = "0000-0001-8260-231X"
EXPECTED_LICENSE = "CC-BY-4.0"
ROCRATE_CONFORMS_TO = "https://w3id.org/ro/crate/1.1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc


def normalize_license(value: str | None) -> str | None:
    if not value:
        return None
    if "creativecommons.org/licenses/by/4.0" in value:
        return EXPECTED_LICENSE
    cleaned = value.strip().upper().replace(" ", "").replace("-", "")
    if cleaned in {"CCBY40", "CCBY4.0"}:
        return EXPECTED_LICENSE
    return value.strip()


def normalize_orcid(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(\d{4}-\d{4}-\d{4}-\d{3}[0-9X])", value)
    return match.group(1) if match else value.strip()


def extract_orcid(entity: dict | None) -> str | None:
    if not isinstance(entity, dict):
        return None
    if entity.get("orcid"):
        return entity.get("orcid")
    if entity.get("@id"):
        return entity.get("@id")
    return None


def parse_citation_cff(path: Path) -> dict:
    text = read_text(path)
    data = {}
    for key in ("title", "license", "version"):
        match = re.search(rf"^{key}:\s*\"?(.+?)\"?\s*$", text, re.M)
        if match:
            data[key] = match.group(1).strip()
    orcid_match = re.search(r"orcid:\s*\"?([^\"\n]+)\"?", text)
    if orcid_match:
        data["orcid"] = orcid_match.group(1).strip()
    return data


def read_readme_title(path: Path) -> str | None:
    for line in read_text(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def find_rocrate_entity(graph: list[dict], entity_id: str) -> dict | None:
    for entity in graph:
        if entity.get("@id") == entity_id:
            return entity
    return None


def listify(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []

    required_paths = [
        "LICENSE",
        "README.md",
        "CITATION.cff",
        "codemeta.json",
        ".zenodo.json",
        "ro-crate-metadata.json",
        "scripts/generate_ro_crate.py",
    ]
    for rel_path in required_paths:
        ensure((REPO_ROOT / rel_path).exists(), f"Missing {rel_path}", errors)

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    readme_title = read_readme_title(REPO_ROOT / "README.md")
    ensure(bool(readme_title), "README.md is missing a top-level title", errors)

    citation = parse_citation_cff(REPO_ROOT / "CITATION.cff")
    ensure("title" in citation, "CITATION.cff missing title", errors)
    ensure("license" in citation, "CITATION.cff missing license", errors)
    ensure("orcid" in citation, "CITATION.cff missing ORCID", errors)

    codemeta = load_json(REPO_ROOT / "codemeta.json")
    ensure(bool(codemeta.get("name")), "codemeta.json missing name", errors)
    ensure(
        bool(codemeta.get("description")),
        "codemeta.json missing description",
        errors,
    )
    ensure(bool(codemeta.get("license")), "codemeta.json missing license", errors)
    ensure(
        bool(codemeta.get("codeRepository")),
        "codemeta.json missing codeRepository",
        errors,
    )
    ensure(bool(codemeta.get("author")), "codemeta.json missing author", errors)

    zenodo = load_json(REPO_ROOT / ".zenodo.json")
    ensure(bool(zenodo.get("title")), ".zenodo.json missing title", errors)
    ensure(
        bool(zenodo.get("description")),
        ".zenodo.json missing description",
        errors,
    )
    ensure(
        bool(zenodo.get("upload_type")),
        ".zenodo.json missing upload_type",
        errors,
    )
    ensure(bool(zenodo.get("creators")), ".zenodo.json missing creators", errors)
    ensure(bool(zenodo.get("license")), ".zenodo.json missing license", errors)

    rocrate = load_json(REPO_ROOT / "ro-crate-metadata.json")
    graph = rocrate.get("@graph", [])
    root_dataset = find_rocrate_entity(graph, "./")
    metadata_descriptor = find_rocrate_entity(graph, "ro-crate-metadata.json")

    ensure(root_dataset is not None, "RO-Crate missing root dataset ./", errors)
    ensure(
        metadata_descriptor is not None,
        "RO-Crate missing metadata descriptor ro-crate-metadata.json",
        errors,
    )

    if metadata_descriptor:
        about = metadata_descriptor.get("about", {})
        about_id = about.get("@id") if isinstance(about, dict) else None
        ensure(about_id == "./", "RO-Crate metadata descriptor not about ./", errors)
        conforms_to = metadata_descriptor.get("conformsTo")
        conforms_ids = [
            item.get("@id")
            for item in listify(conforms_to)
            if isinstance(item, dict)
        ]
        ensure(
            ROCRATE_CONFORMS_TO in conforms_ids,
            "RO-Crate metadata descriptor missing conformsTo RO-Crate 1.1",
            errors,
        )

    titles = {
        "README": readme_title,
        "CITATION": citation.get("title"),
        "CodeMeta": codemeta.get("name"),
        "Zenodo": zenodo.get("title"),
        "RO-Crate": root_dataset.get("name") if root_dataset else None,
    }
    for source, value in titles.items():
        ensure(value == EXPECTED_TITLE, f"{source} title mismatch: {value}", errors)

    licenses = {
        "CITATION": normalize_license(citation.get("license")),
        "CodeMeta": normalize_license(codemeta.get("license")),
        "Zenodo": normalize_license(zenodo.get("license")),
        "RO-Crate": normalize_license(root_dataset.get("license")) if root_dataset else None,
    }
    for source, value in licenses.items():
        ensure(value == EXPECTED_LICENSE, f"{source} license mismatch: {value}", errors)

    codemeta_authors = listify(codemeta.get("author"))
    codemeta_orcid = None
    for author in codemeta_authors:
        codemeta_orcid = extract_orcid(author)
        if codemeta_orcid:
            break

    zenodo_orcid = None
    for creator in listify(zenodo.get("creators")):
        if isinstance(creator, dict) and creator.get("orcid"):
            zenodo_orcid = creator.get("orcid")
            break

    rocrate_orcid = None
    if root_dataset and root_dataset.get("author"):
        author_entry = root_dataset.get("author")
        for author in listify(author_entry):
            rocrate_orcid = extract_orcid(author)
            if rocrate_orcid:
                break
        if not rocrate_orcid:
            author_ids = [
                item.get("@id")
                for item in listify(author_entry)
                if isinstance(item, dict)
            ]
            author_entities = [
                find_rocrate_entity(graph, author_id)
                for author_id in author_ids
                if author_id
            ]
            for author in author_entities:
                rocrate_orcid = extract_orcid(author)
                if rocrate_orcid:
                    break

    orcids = {
        "CITATION": citation.get("orcid"),
        "CodeMeta": codemeta_orcid,
        "Zenodo": zenodo_orcid,
        "RO-Crate": rocrate_orcid,
    }
    for source, value in orcids.items():
        normalized = normalize_orcid(value)
        ensure(
            normalized == EXPECTED_ORCID,
            f"{source} ORCID mismatch: {value}",
            errors,
        )

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        print(f"[FAIL] {len(errors)} issue(s) found.")
        return 1

    print("[PASS] Metadata files validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

