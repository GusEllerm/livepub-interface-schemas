# Publishing & Versioning Guide

## URL Structure

All LivePublication interface schemas are served under:

```
https://livepublication.org/interface-schemas/
```

With w3id persistent identifiers at:

```
https://w3id.org/livepublication/interface-schemas/
```

### Module Layout

Each module (e.g., `dpc`, `dsc`) follows this structure:

```
/interface-schemas/{module}/
├── index.html              # Human-readable landing page (HTML)
├── terms.ttl               # Vocabulary definitions (Turtle)
├── shapes.ttl              # SHACL validation shapes (Turtle)
└── contexts/
    ├── v1.jsonld          # JSON-LD context version 1 (immutable)
    ├── v2.jsonld          # JSON-LD context version 2 (immutable)
    └── ...
```

### URL Patterns

| Resource | URL | MIME Type |
|----------|-----|-----------|
| Module landing (HTML) | `/{module}/` or `/{module}/index.html` | `text/html` |
| Vocabulary (Turtle) | `/{module}/terms.ttl` | `text/turtle` |
| SHACL shapes (Turtle) | `/{module}/shapes.ttl` | `text/turtle` |
| JSON-LD context v1 | `/{module}/contexts/v1.jsonld` | `application/ld+json` |
| Combined context v1 | `/contexts/lp-dscdpc/v1.jsonld` | `application/ld+json` |

## Content Negotiation

Module base URLs support content negotiation:

```bash
# Default: returns HTML landing page
curl https://livepublication.org/interface-schemas/dpc/

# Turtle: returns vocabulary
curl -H "Accept: text/turtle" \
     https://livepublication.org/interface-schemas/dpc/
```

Implementation is handled by the development server (`serve_dev.py`) and should be mirrored in production deployment.

## Versioning Policy

### JSON-LD Contexts (Immutable)

**Rule:** Once published, context versions are **immutable**.

- Versions follow semantic versioning: `v1.jsonld`, `v2.jsonld`, etc.
- **Never** modify an existing version (breaks consumers' caches)
- To make changes: publish a **new version** (`v2.jsonld`)
- Old versions remain available indefinitely

**Caching:** Contexts are served with:
```
Cache-Control: public, max-age=31536000, immutable
```

**Why immutable?**  
JSON-LD documents reference contexts by URL. Changing a context breaks all existing documents that reference it.

### Vocabularies & Shapes (Evolving)

**Rule:** `terms.ttl` and `shapes.ttl` may evolve, following **backwards-compatible** changes.

**Acceptable changes:**
- ✅ Add new classes/properties
- ✅ Add new shapes or constraints
- ✅ Clarify documentation/comments
- ✅ Relax constraints (e.g., remove `sh:maxCount`)

**Breaking changes require:**
- Major version bump in ontology metadata (`owl:versionInfo`)
- Communication to consumers
- Consider publishing as a new module if changes are substantial

## Adding a New Module

### Checklist

1. **Create module directory structure:**
   ```bash
   mkdir -p interface-schemas/{new-module}/contexts
   ```

2. **Create required files:**
   - `interface-schemas/{new-module}/index.html` — Landing page
   - `interface-schemas/{new-module}/terms.ttl` — Vocabulary (Turtle/OWL)
   - `interface-schemas/{new-module}/shapes.ttl` — SHACL shapes
   - `interface-schemas/{new-module}/contexts/v1.jsonld` — JSON-LD context

3. **Update catalog:**
   - Edit `interface-schemas/index.html` to add the new module

4. **Metadata checklist:**
   ```turtle
   # terms.ttl ontology metadata
   <https://livepublication.org/interface-schemas/{new-module}/>
     a owl:Ontology ;
     dct:title "Module Title" ;
     dct:creator "Augustus Ellerm" ;
     dct:contributor "Augustus Ellerm <ael854@aucklanduni.ac.nz>" ;
     dct:license <https://creativecommons.org/licenses/by/4.0/> ;
     dct:issued "YYYY-MM-DD"^^xsd:date ;
     owl:versionInfo "0.1.0" ;
     vann:preferredNamespacePrefix "{prefix}" ;
     vann:preferredNamespaceUri "https://livepublication.org/interface-schemas/{new-module}#" .
   ```

5. **Test locally:**
   ```bash
   make serve
   # Test in browser:
   # http://localhost:8000/interface-schemas/{new-module}/
   
   # Test content negotiation:
   curl -I -H "Accept: text/turtle" \
        http://localhost:8000/interface-schemas/{new-module}/
   
   # Test context:
   curl http://localhost:8000/interface-schemas/{new-module}/contexts/v1.jsonld
   ```

6. **Run validation:**
   ```bash
   make test  # Full test suite
   ```

7. **Open PR:**
   - Branch: `feat/module-{new-module}`
   - Title: `feat: add {new-module} vocabulary and context`
   - Description: Brief purpose and scope

8. **After merge:**
   - Module is automatically served at production URLs
   - w3id redirects work immediately (no w3id changes needed)

## Deployment

### Development Server

```bash
make serve          # Foreground on port 8000
make serve-bg       # Background with PID file
make stop           # Stop background server
```

The development server (`serve_dev.py`) handles:
- Correct MIME types (`.jsonld` → `application/ld+json`, `.ttl` → `text/turtle`)
- CORS headers (`Access-Control-Allow-Origin: *`)
- Immutable caching for versioned contexts

### Production Deployment

Requirements for production server:
1. **MIME types:** Must serve correct Content-Type for `.jsonld` and `.ttl`
2. **CORS:** Must send `Access-Control-Allow-Origin: *` for JSON-LD contexts
3. **Caching:** Versioned contexts (`*/contexts/v*.jsonld`) must send:
   ```
   Cache-Control: public, max-age=31536000, immutable
   ```
4. **Content negotiation:** Module base URLs should serve HTML by default, Turtle with `Accept: text/turtle`

### Server Configuration Examples

**Nginx:**
```nginx
location ~* /interface-schemas/.*/contexts/v[0-9.]+\.jsonld$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header Access-Control-Allow-Origin "*";
}
```

**Apache (.htaccess):**
```apache
<FilesMatch "contexts/v[0-9.]+\.jsonld$">
    Header set Cache-Control "public, max-age=31536000, immutable"
    Header set Access-Control-Allow-Origin "*"
</FilesMatch>
```

## w3id Integration

The w3id.org persistent identifier redirects are configured at:
```
https://github.com/perma-id/w3id.org/tree/master/livepublication/interface-schemas
```

**Generic rules** cover all current and future modules:
- `https://w3id.org/livepublication/interface-schemas/{module}` → module landing or vocabulary
- `https://w3id.org/livepublication/interface-schemas/{module}/contexts/v{N}.jsonld` → versioned context
- Content negotiation supported at module base

**No w3id changes needed** when adding new modules—redirects work automatically.

## Maintenance

### Regular Tasks

- **Test suite:** Run `make test` before committing changes
- **Vocabulary drift:** Monitor `make audit-vocab` for unexpected changes
- **SPARQL policy:** `make audit-sparql` enforces semantic contracts

### Version Bumps

When publishing a new context version:

1. Copy current context:
   ```bash
   cp interface-schemas/{module}/contexts/v1.jsonld \
      interface-schemas/{module}/contexts/v2.jsonld
   ```

2. Make changes in `v2.jsonld`

3. Update module's `index.html` to list new version

4. Update `interface-schemas/index.html` catalog

5. **Never delete or modify old versions**

## Support

**Maintainer:** Augustus Ellerm  
**Email:** ael854@aucklanduni.ac.nz  
**Repository:** https://github.com/GusEllerm/livepub-interface-schemas  
**Issues:** https://github.com/GusEllerm/livepub-interface-schemas/issues
