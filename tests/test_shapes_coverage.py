"""
SHACL shape coverage metrics (diagnostic; non-failing).

Analyzes which shapes are actually exercised by valid crates
and identifies shapes with zero coverage.
"""

import json
import pathlib
from collections import defaultdict
from typing import Dict, Any

import rdflib as rdf
from pyshacl import validate

from tests._example_loader import list_valid_examples
from tests._jsonld_utils import to_rdf_graph_from_jsonld


ARTIFACT_DIR = pathlib.Path(".artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)
COVERAGE_PATH = ARTIFACT_DIR / "shapes_coverage.json"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DPC_SHAPES = REPO_ROOT / "interface-schemas" / "dpc" / "shapes.ttl"
DSC_SHAPES = REPO_ROOT / "interface-schemas" / "dsc" / "shapes.ttl"


def _load_graph(path: pathlib.Path, base_override: str) -> rdf.Graph:
    """Load a JSON-LD crate and convert to rdflib Graph."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return to_rdf_graph_from_jsonld(doc, base_override)


def _load_shapes() -> rdf.Graph:
    """Load combined DPC + DSC shapes."""
    shapes_graph = rdf.Graph()
    shapes_graph.parse(str(DPC_SHAPES), format="turtle")
    shapes_graph.parse(str(DSC_SHAPES), format="turtle")
    return shapes_graph


def _extract_coverage(results_graph: rdf.Graph, data_graph: rdf.Graph) -> Dict[str, Dict[str, Any]]:
    """
    Extract coverage information from SHACL validation results.
    
    Returns dict mapping shape IRI to coverage stats.
    """
    SH = rdf.Namespace("http://www.w3.org/ns/shacl#")
    
    coverage: Dict[str, Dict[str, Any]] = {}
    
    # Find all validation results
    for result in results_graph.subjects(rdf.RDF.type, SH.ValidationResult):
        # Get the source shape
        source_shape = results_graph.value(result, SH.sourceShape)
        if source_shape:
            shape_iri = str(source_shape)
            
            if shape_iri not in coverage:
                coverage[shape_iri] = {
                    "targeted_nodes": set(),
                    "conforms": True,
                    "violations": 0,
                }
            
            # Get the focus node
            focus_node = results_graph.value(result, SH.focusNode)
            if focus_node:
                coverage[shape_iri]["targeted_nodes"].add(str(focus_node))
            
            # Track violations
            severity = results_graph.value(result, SH.resultSeverity)
            if severity == SH.Violation:
                coverage[shape_iri]["conforms"] = False
                coverage[shape_iri]["violations"] += 1
    
    # Convert sets to lists for JSON serialization
    for shape_iri in coverage:
        coverage[shape_iri]["targeted_nodes"] = sorted(list(coverage[shape_iri]["targeted_nodes"]))
        coverage[shape_iri]["node_count"] = len(coverage[shape_iri]["targeted_nodes"])
    
    return coverage


def test_shapes_coverage_report(server_base):
    """
    Generate SHACL shape coverage report (non-failing).
    
    Writes .artifacts/shapes_coverage.json with per-shape coverage stats.
    Prints shapes with zero coverage.
    """
    shapes_graph = _load_shapes()
    
    # Aggregate coverage across all valid crates
    all_shapes_seen: Dict[str, Dict[str, Any]] = {}
    cwd = pathlib.Path.cwd()
    
    for crate_path_str in list_valid_examples():
        crate_path = pathlib.Path(crate_path_str)
        try:
            rel_path = str(crate_path.relative_to(cwd))
        except ValueError:
            rel_path = str(crate_path)
        
        try:
            data_graph = _load_graph(crate_path, server_base)
        except Exception as e:
            print(f"[SHAPES COVERAGE] Warning: could not load {rel_path}: {e}")
            continue
        
        # Run SHACL validation
        try:
            conforms, results_graph, results_text = validate(
                data_graph,
                shacl_graph=shapes_graph,
                inference='none',
                advanced=True,
                do_owl_imports=False,
            )
        except Exception as e:
            print(f"[SHAPES COVERAGE] Warning: validation failed for {rel_path}: {e}")
            continue
        
        # Extract coverage from this file
        file_coverage = _extract_coverage(results_graph, data_graph)
        
        for shape_iri, stats in file_coverage.items():
            if shape_iri not in all_shapes_seen:
                all_shapes_seen[shape_iri] = {
                    "files": [],
                    "total_nodes": 0,
                    "total_violations": 0,
                    "example_nodes": set(),
                }
            
            all_shapes_seen[shape_iri]["files"].append(rel_path)
            all_shapes_seen[shape_iri]["total_nodes"] += stats["node_count"]
            all_shapes_seen[shape_iri]["total_violations"] += stats["violations"]
            # stats["targeted_nodes"] is now a list
            all_shapes_seen[shape_iri]["example_nodes"].update(stats["targeted_nodes"][:5])
    
    # Convert to serializable format
    coverage_report: Dict[str, Any] = {}
    for shape_iri, stats in all_shapes_seen.items():
        coverage_report[shape_iri] = {
            "files": stats["files"],
            "total_nodes": stats["total_nodes"],
            "total_violations": stats["total_violations"],
            "example_nodes": sorted(list(stats["example_nodes"]))[:10],
        }
    
    # Find all defined shapes (to identify zero-coverage shapes)
    SH = rdf.Namespace("http://www.w3.org/ns/shacl#")
    all_defined_shapes = set()
    for shape in shapes_graph.subjects(rdf.RDF.type, SH.NodeShape):
        all_defined_shapes.add(str(shape))
    
    zero_coverage = sorted(all_defined_shapes - set(coverage_report.keys()))
    
    coverage_report["_meta"] = {
        "total_shapes_defined": len(all_defined_shapes),
        "shapes_exercised": len(coverage_report) - 1,  # Exclude _meta itself
        "zero_coverage_shapes": zero_coverage,
    }
    
    # Write artifact
    with open(COVERAGE_PATH, "w", encoding="utf-8") as fh:
        json.dump(coverage_report, fh, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n=== SHACL Shape Coverage Report ===")
    print(f"[COVERAGE] Total shapes defined: {len(all_defined_shapes)}")
    print(f"[COVERAGE] Shapes exercised: {len(coverage_report) - 1}")
    print(f"[COVERAGE] Zero-coverage shapes: {len(zero_coverage)}")
    
    if zero_coverage:
        print("\n[COVERAGE] Shapes with zero coverage:")
        for shape_iri in zero_coverage[:10]:
            print(f"  - {shape_iri}")
        if len(zero_coverage) > 10:
            print(f"  ... and {len(zero_coverage) - 10} more")
    
    print(f"\n[COVERAGE] Artifact written to: {COVERAGE_PATH.absolute()}")
    print("=" * 40)
    
    # Always pass - this is diagnostic only
    assert True
