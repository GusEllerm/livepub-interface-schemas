# DSC Profile Validation Report

Version and timestamp: 2026-01-16T07:16:32Z

## Files validated
- `interface-schemas/dsc/index.html`
- `interface-schemas/dsc/terms.ttl`
- `interface-schemas/dsc/shapes.ttl`
- `interface-schemas/dsc/contexts/v1.jsonld`
- `interface-schemas/dpc/shapes.ttl`
- `interface-schemas/contexts/lp-dscdpc/v1.jsonld`
- `interface-schemas/vendor/ro-crate/1.1/context.jsonld`

## Validation checklist
### 1) DSC entity graph (structural)
- Step descriptor -> step -> HowToStep: ✅ present and documented
- Step descriptor -> hasPart -> HardwareRuntime: ✅ present and documented
- HardwareRuntime -> component -> HardwareComponent: ✅ present and documented
- HardwareComponent -> performance -> Observation: ✅ optional and documented
- MediaSubscription/authenticator/Organization links: ⚠️ guidance only (not in DSC/DPC shapes)
- object/result -> File or PropertyValue: ✅ present and documented

### 2) Repo artifacts (terms/shapes/contexts)
Key properties/types used in tables, normative statements, and examples:
- `DistributedStep`: ✅ `dsc/terms.ttl`, `dsc/contexts/v1.jsonld`
- `HardwareRuntime`, `HardwareComponent`, `component`, `performance`: ✅ `dpc/shapes.ttl`, `contexts/lp-dscdpc/v1.jsonld`
- `HowToStep`, `step`, `position`, `identifier`, `sourceOrganization`: ✅ `dsc/shapes.ttl`, `contexts/lp-dscdpc/v1.jsonld`
- `object`, `result`, `hasPart`, `mainEntity`: ✅ `dsc/shapes.ttl`, `contexts/lp-dscdpc/v1.jsonld`
- `Observation`, `observationAbout`, `measurementTechnique`, `value`: ✅ `dpc/shapes.ttl`, `contexts/lp-dscdpc/v1.jsonld`
- `Dataset`, `conformsTo`: ✅ `vendor/ro-crate/1.1/context.jsonld`
- `CreateAction`, `HowTo`, `File`, `Schedule`, `ActionAccessSpecification`: ✅ schema.org terms via `@vocab` in `contexts/lp-dscdpc/v1.jsonld`
- `MediaSubscription`, `authenticator`: ⚠️ not found in DSC/DPC shapes or contexts; retained as guidance only
- `Profile` contextual entity: ⚠️ not defined in DSC/DPC artifacts; mentioned as guidance

### 3) Thesis correction: WMS task UUID placement
- Text requirements: ✅ UUID stored in `HowToStep.identifier`
- Tables: ✅ `position` reserved for integer order; `identifier` used for WMS UUID
- Examples: ✅ UUID placed in `HowToStep.identifier`
- Why: This aligns with SHACL expectations for `position` and preserves a stable place for the WMS task identifier.

## Observed issues (before changes)
- WMS task UUID guidance and example used `position` instead of `identifier`.
- Draft banner lacked a stabilisation plan.
- Minimal example did not include `contexts/v1.jsonld` in `@context`.
- Recommended typing conventions were not explicit.
- No explicit "validated vs guidance" separation.
- Conformance declaration was not prominent.

## Changes applied
- Added a draft stabilisation plan bullet list.
- Updated WMS task UUID guidance to use `HowToStep.identifier`, adjusted tables and example.
- Added recommended typing subsection and expanded step descriptor types in the example.
- Added `contexts/v1.jsonld` to the example `@context`.
- Added a "validated vs guidance" section to clarify SHACL enforcement.
- Added a prominent conformance declaration callout near the top.

## Open questions / remaining risks
- `MediaSubscription`/`authenticator` are not defined in the DSC/DPC artifacts; consider adding to contexts/shapes or treating as out-of-scope.
- `Profile` contextual entity is referenced as guidance but not defined in DSC/DPC artifacts.

## Next recommended step
- Update at least one canonical DSC example crate to include `conformsTo` with the DSC profile URI and to demonstrate UUID placement in `HowToStep.identifier`.
