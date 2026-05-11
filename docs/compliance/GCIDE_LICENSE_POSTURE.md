# GCIDE GPL License Posture — WordPower

> **Status:** PENDING legal sign-off — do not ship the GCIDE-derived etymology overlay until this document records a signed-off distribution model.

Related: [ROOT_FAMILIES_DECISION.md](../architecture/ROOT_FAMILIES_DECISION.md) | [Spike B FINDINGS.md](../../spikes/morphology-engine/b-skeat-websters/FINDINGS.md) | WordPower-app issue #531

---

## 1. Background

Spike B selected **GCIDE 0.54** (the GNU-maintained Webster's 1913 corpus) as the etymology overlay source for the morphology engine. GCIDE is licensed under **GPL 3.0+**. The 1913 Webster's base text is public domain, but GCIDE's structure, annotations, and supplements are GPL-licensed works.

This document tracks the legal posture decision required before any user-visible release that ships a GCIDE-derived data bundle.

---

## 2. Distribution Models Under Consideration

### Model A — Runtime-loaded data file, distributed separately (preferred)

Bundle the GCIDE-derived morphology data as a standalone data file that is:
- Downloaded or installed separately from the app binary
- Loaded at runtime by the app
- Accompanied by full attribution and the GPL 3.0 COPYING notice

**Rationale:** Distributing GPL-licensed content as a separable data artefact rather than compiled into the binary reduces co-licensing exposure for the proprietary app layer.

**Requires:** Legal counsel confirmation that this structure satisfies GPL §2/§6 obligations without triggering copyleft propagation to the app itself.

### Model B — Reduced derivative bundle (backup)

Extract only the §6 schema fields (morpheme, meaning, language, canonical\_root, etymology source-form) into a lean bundle. Full GCIDE prose etymology is excluded. Bundle is license-tagged with attribution.

**Rationale:** Smaller footprint, less textual copying, potentially clearer public-domain/GPL boundary.

**Requires:** Legal counsel confirmation that the extracted fields alone do not constitute a GPL-covered derived work.

### Model C — Drop GCIDE overlay (fallback)

Remove the GCIDE etymology layer entirely. Use the `etymology` field from the Wikipedia roots corpus instead (§9 row 5 of the risk register).

**Use when:** Models A and B are both rejected by legal review.

---

## 3. Attribution Requirements (all models)

Regardless of the chosen distribution model, every release that ships GCIDE-derived content **must** include:

- The GCIDE COPYING notice (GPL 3.0 text)
- Attribution: "Etymology data derived from GCIDE 0.54, Copyright (C) 1999 GCIDE contributors, licensed under GPL 3.0+"
- Notice location: Settings → Open-Source Licenses screen **and** a `COPYING.gcide` file bundled alongside the data artefact

---

## 4. Decision Record

| Date | Reviewer | Model chosen | Notes / sign-off reference |
|------|----------|--------------|---------------------------|
| —    | PENDING  | —            | — |

> **Gate:** This table must have at least one row with a signed-off model before the morphology bundle is included in any release build.

---

## 5. Release Checklist Integration

The morphology bundle release checklist (see WordPower-app `docs/release/MORPHOLOGY_BUNDLE_CHECKLIST.md`) must include:

- [ ] GCIDE_LICENSE_POSTURE.md decision record is signed off (non-PENDING)
- [ ] COPYING.gcide is present in the data bundle
- [ ] In-app Open-Source Licenses screen lists GCIDE attribution
- [ ] Distribution model matches the signed-off posture

---

## 6. Open Questions

- Does bundling the GCIDE data in a Play Store / App Store binary (even as a separate download) trigger GPL propagation to the app itself? *(Needs legal answer)*
- If Model A is chosen, does the "separate distribution" requirement mean a separate Firebase Storage download, or can it be packaged as an app asset? *(Needs legal clarification)*

---

*Last updated: 2026-05-11 — initial draft, awaiting legal review (WP-531)*
