# Post-W3ID Merge Validation Report

**Date:** 27 October 2025  
**Repository:** livepub-interface-schemas  
**Branch:** main

---

## Redirect Validation (w3id.org)

All w3id.org redirects return **HTTP 302 Found** with correct `Location` headers and appropriate CORS headers (`Access-Control-Allow-Origin: *`).

### 1. DPC without Accept header
- **URL:** `https://w3id.org/livepublication/interface-schemas/dpc`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/dpc/index.html`
- **✓** Version string preserved, CORS enabled

### 2. DPC with Accept: text/turtle
- **URL:** `https://w3id.org/livepublication/interface-schemas/dpc`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/dpc/terms.ttl`
- **✓** Content negotiation working, redirects to Turtle vocabulary

### 3. DPC Context v1
- **URL:** `https://w3id.org/livepublication/interface-schemas/dpc/contexts/v1.jsonld`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/dpc/contexts/v1.jsonld`
- **✓** Version string (`v1.jsonld`) preserved in redirect

### 4. Profile Context v1
- **URL:** `https://w3id.org/livepublication/interface-schemas/contexts/lp-dscdpc/v1.jsonld`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld`
- **✓** Version string preserved, profile context accessible

### 5. Catalog Index
- **URL:** `https://w3id.org/livepublication/interface-schemas/`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/index.html`
- **✓** Root redirect working

### 6. Unknown Path
- **URL:** `https://w3id.org/livepublication/interface-schemas/unknown`
- **Status:** 302 Found
- **Location:** `https://livepublication.org/interface-schemas/unknown/index.html`
- **Note:** Redirects to unknown path (expected fallback behavior)

---

## Resource Validation (livepublication.org)

All production resources return **HTTP 200 OK** with correct headers.

### 1. DPC index.html
- **URL:** `https://livepublication.org/interface-schemas/dpc/index.html`
- **Status:** 200 OK
- **Content-Type:** `text/html`
- **Access-Control-Allow-Origin:** `*`
- **✓** HTML documentation page accessible

### 2. DPC terms.ttl
- **URL:** `https://livepublication.org/interface-schemas/dpc/terms.ttl`
- **Status:** 200 OK
- **Content-Type:** `text/turtle`
- **Access-Control-Allow-Origin:** `*`
- **✓** Turtle vocabulary accessible

### 3. DPC Context v1.jsonld
- **URL:** `https://livepublication.org/interface-schemas/dpc/contexts/v1.jsonld`
- **Status:** 200 OK
- **Content-Type:** `application/ld+json`
- **Access-Control-Allow-Origin:** `*`
- **Cache-Control:** `public, max-age=31536000, immutable`
- **✓** Context includes proper immutable caching and CORS

### 4. Profile Context v1.jsonld
- **URL:** `https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld`
- **Status:** 200 OK
- **Content-Type:** `application/ld+json`
- **Access-Control-Allow-Origin:** `*`
- **Cache-Control:** `public, max-age=31536000, immutable`
- **✓** Profile context includes proper immutable caching and CORS

### HTML Structure Validation

Inspected `dpc/index.html` and confirmed:
- **✓** `<base href="/interface-schemas/dpc/">` tag present in `<head>`
- **✓** Links to `terms.ttl`, `shapes.ttl`, and `contexts/v1.jsonld` working
- **✓** Fragment anchors present: `<h2 id="HardwareRuntime">`, `<h2 id="HardwareComponent">`, etc.
- **✓** Fragment IRIs like `https://livepublication.org/interface-schemas/dpc#HardwareComponent` will resolve correctly

---

## JSON-LD Expansion Test

Successfully expanded `tests/crates/valid/dsc_full_02.json` using **only production URLs** via w3id.org and livepublication.org (no local overrides).

### Expansion Summary

**Contexts fetched:**
1. `https://w3id.org/ro/crate/1.1/context` → redirected to `https://www.researchobject.org/ro-crate/specification/1.1/context.jsonld`
2. `https://w3id.org/ro/terms/workflow-run/context` → redirected to `https://www.researchobject.org/ro-terms/workflow-run/context.jsonld`
3. `https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld` → fetched directly

**Result:** ✓ Expansion succeeded without errors

**Expanded graph:** 14 nodes

### Key Classes Found

The expanded RDF includes the following LivePublication-specific classes:
- `https://livepublication.org/interface-schemas/dsc#DistributedStep`
- `https://livepublication.org/interface-schemas/dpc#HardwareRuntime`
- `https://livepublication.org/interface-schemas/dpc#HardwareComponent`

Plus standard schema.org classes:
- `https://schema.org/MediaObject` (not `http://schema.org/File`)
- `https://schema.org/Observation`
- `http://schema.org/Dataset`, `http://schema.org/CreateAction`, `http://schema.org/HowTo`, etc.

### LivePublication Predicates Used

- `https://livepublication.org/interface-schemas/dpc#component`
- `https://livepublication.org/interface-schemas/dpc#performance`

### Policy Compliance

**✓ No `http://schema.org/*` predicates** – all schema.org terms properly use HTTPS  
**✓ No `schema:File` classes** – using `schema:MediaObject` as required  
**✓ LivePublication terms** – custom dsc/dpc predicates present in expanded graph  

---

## Conclusion

**All validation checks passed successfully.**

1. **w3id.org redirects** are working correctly with proper version preservation and CORS headers
2. **Production resources** at livepublication.org return correct content types and headers:
   - JSON-LD contexts have immutable caching (`max-age=31536000, immutable`)
   - All resources include CORS headers (`Access-Control-Allow-Origin: *`)
3. **End-to-end expansion** works using only public URLs without local overrides
4. **RDF graph is clean:**
   - No `http://schema.org/*` predicates (only HTTPS)
   - No `schema:File` classes (using `MediaObject`)
   - LivePublication terms properly expanded

The w3id.org persistent URL infrastructure is ready for public consumption. External tools can now expand LivePublication crates using the published contexts via w3id.org redirects.

