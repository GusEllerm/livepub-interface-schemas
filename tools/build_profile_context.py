#!/usr/bin/env python3
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DPC_DEFAULT = ROOT / "interface-schemas" / "dpc" / "contexts" / "v1.jsonld"
DSC_DEFAULT = ROOT / "interface-schemas" / "dsc" / "contexts" / "v1.jsonld"
OUT_DEFAULT = ROOT / "interface-schemas" / "contexts" / "lp-dscdpc" / "v1.jsonld"

SCHEMA_BLOCK = {
    "@vocab": "https://schema.org/",
    "schema": "https://schema.org/",
    # Commonly-used schema terms explicitly remapped to HTTPS to override RO-Crate's HTTP mappings
    # Core text/value terms
    "name": "schema:name",
    "description": "schema:description",
    "value": "schema:value",
    # Linking/container terms
    "hasPart": {"@id": "schema:hasPart", "@type": "@id"},
    "step": {"@id": "schema:step", "@type": "@id"},
    "additionalProperty": {"@id": "schema:additionalProperty", "@type": "@id"},
    # HowToStep terms
    "position": "schema:position",
    "identifier": "schema:identifier",
    "sourceOrganization": {"@id": "schema:sourceOrganization", "@type": "@id"},
    "requiresSubscription": "schema:requiresSubscription",
    # Observation terms
    "Observation": "schema:Observation",
    "PropertyValue": "schema:PropertyValue",
    "observationAbout": {"@id": "schema:observationAbout", "@type": "@id"},
    "measurementTechnique": "schema:measurementTechnique",
    "minValue": "schema:minValue",
    "maxValue": "schema:maxValue",
    "valueReference": {"@id": "schema:valueReference", "@type": "@id"},
    "image": {"@id": "schema:image", "@type": "@id"},
    # I/O terms (CreateAction-aligned)
    "object": {"@id": "schema:object", "@type": "@id"},
    "result": {"@id": "schema:result", "@type": "@id"},
    # RO-Crate terms that expand to HTTP in the upstream context
    "File": "https://schema.org/MediaObject",  # RO-Crate maps File→MediaObject; ensure HTTPS
    "about": {"@id": "schema:about", "@type": "@id"},
    "actionStatus": "schema:actionStatus",
    "additionalType": "schema:additionalType",
    "agent": {"@id": "schema:agent", "@type": "@id"},
    "alternateName": "schema:alternateName",
    "applicationCategory": "schema:applicationCategory",
    "contentSize": "schema:contentSize",
    "datePublished": {"@id": "schema:datePublished", "@type": "xsd:date"},
    "email": "schema:email",
    "encodingFormat": "schema:encodingFormat",
    "endTime": {"@id": "schema:endTime", "@type": "xsd:dateTime"},
    "exampleOfWork": {"@id": "schema:exampleOfWork", "@type": "@id"},
    "familyName": "schema:familyName",
    "free": "schema:free",
    "givenName": "schema:givenName",
    "instrument": {"@id": "schema:instrument", "@type": "@id"},
    "license": {"@id": "schema:license", "@type": "@id"},
    "mainEntity": {"@id": "schema:mainEntity", "@type": "@id"},
    "programmingLanguage": {"@id": "schema:programmingLanguage", "@type": "@id"},
    "startTime": {"@id": "schema:startTime", "@type": "xsd:dateTime"},
    "url": {"@id": "schema:url", "@type": "@id"},
    "version": "schema:version",
    "workExample": {"@id": "schema:workExample", "@type": "@id"},
}

PROV_BLOCK = {
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "prov": "http://www.w3.org/ns/prov#",
    "used":          { "@id": "prov:used",          "@type": "@id" },
    "generated":     { "@id": "prov:generated",     "@type": "@id" },
    "startedAtTime": { "@id": "prov:startedAtTime", "@type": "xsd:dateTime" },
    "endedAtTime":   { "@id": "prov:endedAtTime",   "@type": "xsd:dateTime" }
}

def load_context(path: pathlib.Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    ctx = data.get("@context", data)
    if not isinstance(ctx, dict):
        raise SystemExit(f"Context at {path} must be a JSON object.")
    return ctx

def merge_contexts(*ctx_dicts):
    merged = {}
    for ctx in ctx_dicts:
        for k, v in ctx.items():
            if k in merged and merged[k] != v:
                raise SystemExit(f"Conflict on term '{k}': {merged[k]} vs {v}")
            merged[k] = v
    return merged

def main():
    ap = argparse.ArgumentParser(description="Build lp-dscdpc profile context from module contexts.")
    ap.add_argument("--dpc", type=pathlib.Path, default=DPC_DEFAULT)
    ap.add_argument("--dsc", type=pathlib.Path, default=DSC_DEFAULT)
    ap.add_argument("--out", type=pathlib.Path, default=OUT_DEFAULT)
    ap.add_argument("--check", action="store_true", help="Exit nonzero if OUT is out-of-sync.")
    args = ap.parse_args()

    dpc_ctx = load_context(args.dpc)
    dsc_ctx = load_context(args.dsc)
    merged = merge_contexts(dpc_ctx, dsc_ctx, SCHEMA_BLOCK, PROV_BLOCK)

    out_obj = {"@context": merged}
    out_text = json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not args.out.exists():
            print("Profile OUT file missing:", args.out, file=sys.stderr)
            sys.exit(1)
        committed = args.out.read_text(encoding="utf-8")
        if committed != out_text:
            print("Profile context is out of sync with module contexts.", file=sys.stderr)
            sys.exit(1)
        print("Profile context is up-to-date.")
        return

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_text, encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
