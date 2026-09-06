# When Character learning begins and finishes

Updated 2026-09-06. Learning starts in **TASK-004**, which completed Index Steward's Bogle foundation. **TASK-005** has now started the Value and Trend pilot specialists with one bounded opening checkpoint each. Neither task automatically completes every Character's curriculum.

Here, learning means source-grounded reading, critique, versioned constitution changes, cited memory and theory cards. It is not fine-tuning model weights. Reading also does not establish profitable trading or prospective evaluation readiness.

| Character | Where work starts in the current queue | What that task actually requires | Completed reading today |
| --- | --- | --- | --- |
| Index Steward | TASK-004 | Ordered-learning engine and first real foundation | 1 of 4 books: Bogle |
| Value Rationalist | TASK-005 | Constitution/curriculum and at least one real checkpoint while preserving readiness truth | 0 of 4 books; introduction checkpoint only |
| Systematic Trend Operator | TASK-005 | Constitution/curriculum and at least one real checkpoint while preserving readiness truth | 0 of 4 books; chapter 1 checkpoint only |
| Market Microstructure Mechanic | TASK-021, after 003, 004, 011 and 016 | Specialist checkpoints and execution research using the revised scope | 0 of 7 sources: draft excerpts, Johnson, five papers |
| Probabilistic Risk Skeptic | TASK-021 | Specialist curricula/checkpoints and stress research | 0 of 4 books |
| Event and Disclosure Detective | TASK-022 | Curriculum/source plan and disclosure interface; full reading is not an acceptance criterion | 0 of 4 books |
| Mean-Reversion Experimentalist | Not explicitly assigned a learning task | Later specialist expansion can be scoped through TASK-023 | 0 of 4 books |

The [active queue](../tasks/README.md) exposes the real pilot readiness prerequisite in Step 10 and later Microstructure/Event scopes in Steps 16/17. The historical IDs above locate earlier evidence. Reading may continue earlier within its bounded authorization; Step 10 does not require all seven complete curricula.

## Completing an entire curriculum

No existing task promises all required reading for every Character. After each Character's setup, additional bounded reading runs can use the TASK-004 engine; they need not wait for the remaining engineering sequence. Operational tasks retain their dependencies and readiness gates. Full Event and Mean-Reversion learning needs a separately scoped work item; cataloging material does not launch it.

For each continuation:

1. Select the supplied edition from the [current catalog](../library/catalog/characters.json). Pin the curriculum version, source order, material scope and any accepted excerpt authority. Preserve earlier frozen versions and recheck source/transcript fingerprints. Register source identity, intended use and authorization for the run.
2. Establish the coverage map for the declared material. Use the supplied page-indexed transcripts for Johnson and O'glove. The private `pages_from_transcript` loader verifies the registered text hash and exact page sequence; it does not claim perfect OCR or perform learning. Check ambiguous text, tables, figures and formulae against the source pages while reading. Do not generate replacement OCR by default.
3. Freeze the Character's prior before exposing the next unread source. Read in curriculum and source order with bounded calls, attributed claims, adversarial review and explicit accept/qualify/reject decisions. Shared source files still require separate Character-specific assimilation.
4. Validate the declared coverage, checkpoint chain, memory delta, consolidated memory and any theory/test pair. Preserve contradictions and excluded material. Complete that source's reviewed sections before proceeding.
5. Report completed sources against the pinned curriculum: four books for each original specialist, or seven declared sources for Microstructure v2. A completed approved excerpt remains labeled as an excerpt; it is never counted as the full published book.

The engine supports `full_book`, `full_paper` and `approved_excerpt` completion. Papers and excerpts require explicit scope in the pinned curriculum; excerpts also require recorded scope authority. Existing samples and fixtures remain partial. The predecessor check requires completion of the exact preceding source and its declared scope.

The current `learn --character index_steward` command reports the audited foundation; it does not autonomously read a directory. The Bogle importer remains specific to its existing review. Other sources require their own reviewed artifacts and registration through the learning API.

## Current material availability

All **31 active positions** have local material: **30 PDFs and two derivative transcripts** across seven Characters. Expectations Investing is shared by Value and Event. The [inventory](../library/catalog/INVENTORY_REPORT.md) records actual editions, hashes and remaining text/coverage preparation. Against the Gods retains an unresolved exact edition; its supplied copy is pinned by hash and does not require another acquisition search.

The owner [accepted](../decisions/records/ADR-002-microstructure-reading-scope.md) Harris's 113-page draft excerpts and the [five-paper replacement sequence](microstructure-alternatives.md). The missing original books are retired acquisition targets. No further material search or new OCR generation is required for this plan. Normal source preparation and reading still remain; no new Character training was performed by this update.
