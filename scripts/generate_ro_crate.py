#!/usr/bin/env python3
from pathlib import Path

from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
from rocrate.model.person import Person


TITLE = "LivePublication Interface Schemas"
DESCRIPTION = (
    "LivePublication interface schemas covering DPC/DSC vocabularies, "
    "SHACL shapes, and JSON-LD contexts for distributed provenance-aware "
    "workflow execution."
)
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
VERSION = "0.1.0"
ORCID = "https://orcid.org/0000-0001-8260-231X"


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    crate = ROCrate()

    author = Person(
        crate,
        "#augustus-ellerm",
        properties={"name": "Augustus Ellerm", "orcid": ORCID},
    )
    crate.add(author)

    root = crate.root_dataset
    root["name"] = TITLE
    root["description"] = DESCRIPTION
    root["license"] = LICENSE_URL
    root["version"] = VERSION
    root["author"] = author

    main_entity = ContextEntity(
        crate,
        "#livepublication-interface-schemas",
        properties={"@type": "CreativeWork", "name": TITLE, "description": DESCRIPTION},
    )
    crate.add(main_entity)
    root["mainEntity"] = main_entity

    key_files = [
        {
            "path": "interface-schemas/index.html",
            "description": "Landing page for the LivePublication interface schemas.",
            "encodingFormat": "text/html",
        },
        {
            "path": "interface-schemas/dpc/index.html",
            "description": "DPC vocabulary landing page.",
            "encodingFormat": "text/html",
        },
        {
            "path": "interface-schemas/dpc/terms.ttl",
            "description": "DPC vocabulary (Turtle).",
            "encodingFormat": "text/turtle",
        },
        {
            "path": "interface-schemas/dpc/shapes.ttl",
            "description": "DPC SHACL shapes.",
            "encodingFormat": "text/turtle",
        },
        {
            "path": "interface-schemas/dpc/contexts/v1.jsonld",
            "description": "DPC JSON-LD context v1.",
            "encodingFormat": "application/ld+json",
        },
        {
            "path": "interface-schemas/dsc/index.html",
            "description": "DSC vocabulary landing page.",
            "encodingFormat": "text/html",
        },
        {
            "path": "interface-schemas/dsc/terms.ttl",
            "description": "DSC vocabulary (Turtle).",
            "encodingFormat": "text/turtle",
        },
        {
            "path": "interface-schemas/dsc/shapes.ttl",
            "description": "DSC SHACL shapes.",
            "encodingFormat": "text/turtle",
        },
        {
            "path": "interface-schemas/dsc/contexts/v1.jsonld",
            "description": "DSC JSON-LD context v1.",
            "encodingFormat": "application/ld+json",
        },
        {
            "path": "interface-schemas/contexts/lp-dscdpc/v1.jsonld",
            "description": "Merged DPC/DSC profile JSON-LD context (lp-dscdpc) v1.",
            "encodingFormat": "application/ld+json",
        },
    ]

    for item in key_files:
        file_path = repo_root / item["path"]
        if not file_path.exists():
            raise FileNotFoundError(f"Missing expected file: {file_path}")
        crate.add_file(
            source=file_path.as_posix(),
            dest_path=item["path"],
            properties={
                "description": item["description"],
                "encodingFormat": item["encodingFormat"],
            },
        )

    try:
        crate.metadata_descriptor["conformsTo"] = {
            "@id": "https://w3id.org/ro/crate/1.1"
        }
    except AttributeError:
        pass

    crate.write(repo_root.as_posix())


if __name__ == "__main__":
    main()

