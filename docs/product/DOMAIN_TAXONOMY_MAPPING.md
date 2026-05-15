# Domain Taxonomy Mapping

Resolves the auto-suggest classifier's flat 10-domain pragmatic list to the canonical 15-leaf hierarchy in [PROJECT.md §2.6 Axis 1](PROJECT.md#axis-1-semantic-domain-tree).

- **Decision:** [WP-665](https://github.com/AnunnakiCosmoCrew/WordPower-app/issues/665) (2026-05-15) — keep both taxonomies with a mapping (Option B).
- **Why a mapping exists:** the spike ([FINDINGS.md §5.4](../../spikes/embedding-domain-suggestions/FINDINGS.md#54-divergence-from-projectmd)) showed the classifier is more accurate on a flat pragmatic set, while the 15-leaf hierarchy is the right user-facing organization for browse/discovery.
- **Invariant:** the flat codes below are an implementation detail of [`DomainClassifier`](https://github.com/AnunnakiCosmoCrew/WordPower-app/blob/main/backend/src/main/java/com/wordpower/api/dictionary/DomainClassifier.java). Anything user-visible (filter chips, picker rows, word-detail badge) renders the **hierarchy leaf**, resolved via this table.

## Flat → leaf

| Flat code (classifier) | Hierarchy leaf (displayed) | Branch |
|---|---|---|
| `Law` | Law & Politics | Society |
| `Business` | Work & Business | Society |
| `Finance` | Work & Business | Society |
| `Engineering` | Science & Technology | The Physical World |
| `Medicine` | Body & Health | The Physical World |
| `Science` | Science & Technology | The Physical World |
| `Technology` | Science & Technology | The Physical World |
| `Learning` | Thinking & Learning | The Mind |
| `Arts` | Culture & Arts | Society |
| `Daily Life` | Daily Life | Society |
| `Other` | *(no auto-suggestion — picker opens with no preselection)* | — |

## Notes

- **Many-to-one collapses are intentional.** `Engineering`, `Science`, `Technology` all resolve to *Science & Technology*; `Business` and `Finance` both resolve to *Work & Business*. The flat list is a finer-grained internal accelerator (better keyword separability for the classifier); the leaf is the user-facing vocabulary.
- **Leaves the classifier never emits.** Nine of the fifteen hierarchy leaves have no flat-code source: *Nature, Food & Drink, Home & Living, Emotions & Feelings, Communication, Character & Personality, Travel & Places, Relationships, Religion/Belief* (if/when added). Words in these areas are reachable through the manual picker only — the classifier returns `Other` (no suggestion). This is acceptable per the spike: these categories are sparse in user-capture corpora, and silent-on-uncertainty beats wrong-with-confidence.
- **Evolving the mapping.** When a flat code is added or renamed (e.g., splitting `Science` into `Biology`/`Physics`), update this table *and* PROJECT.md §Axis 1 if a new leaf is needed. When a leaf is renamed in PROJECT.md, update the right column here in the same commit.
