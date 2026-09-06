# ADR-002: Use the supplied Microstructure draft and research packet

- Status: accepted by the owner, 2026-09-05
- Catalog revision: `microstructure-supplied-material-v2`, inventory schema version 2
- Predecessor: catalog at commit `e0f9e8454665e74193def2aa19f791c60e3ca8ab`

The owner supplied the five previously proposed papers and OCR transcripts for Johnson and O'glove, requested adoption of the replacements, and chose to retain Trading and Exchanges (draft) rather than continue searching for a complete published copy. The reference to README section 4 was a numbering mismatch: the two missing titles belong to the Market Microstructure Mechanic in section 5. Mean-Reversion's four sources remain unchanged.

The revised Microstructure order is:

1. Trading and Exchanges (draft), Larry Harris: all 113 supplied PDF pages, explicitly limited excerpts.
2. Algorithmic Trading and DMA, Barry Johnson: supplied scan with its 595-page-indexed transcript.
3. How markets slowly digest changes in supply and demand, Bouchaud, Farmer and Lillo.
4. Limit Order Books, Gould and coauthors.
5. Market Microstructure Knowledge Needed for Controlling an Intra-Day Trading Process, Lehalle.
6. Optimal split of orders across liquidity pools: a stochastic algorithm approach, Laruelle, Lehalle and Pagès.
7. Realtime market microstructure analysis: online Transaction Cost Analysis, Azencott and coauthors.

Positions 3–4 replace Trades, Quotes and Prices; positions 5–7 replace Market Microstructure in Practice. The missing books become retired acquisition targets, retained in catalog history. No further reading-material search is required by this plan. The original book curriculum remains historically incomplete; completion of the revised curriculum means the declared draft scope, Johnson and five papers have been reviewed in order.

Harris's omitted material remains unknown. Accepting its scope does not turn its excerpts into the published book, establish equivalent coverage, or authorize performance claims. The learning engine records `approved_excerpt` separately from `full_book` and `full_paper`. Excerpt completion requires explicit scope authority in the pinned curriculum, verified coverage of the declared material and completion of its sections. Ordinary samples and fixtures still cannot be promoted to completed reading.

The two supplied transcripts are derivatives of their respective scans. Their file hashes, parent PDF hashes, sequential page counts and empty-text page numbers are recorded. Page indexing was verified; exhaustive word, equation and table accuracy was not. Use the existing text and resolve ambiguities against the original pages as part of reading; no replacement OCR job is needed.

This decision updates acquisition and source selection. It does not claim that any new source has been learned, change the completed Bogle artifacts, start a paid/recurring run or advance a Character's trading readiness.
