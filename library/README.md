# Library

The [current inventory](catalog/INVENTORY_REPORT.md) covers all seven Characters and **31 active reading positions**. Its [machine-readable catalog](catalog/characters.json) records **30 local PDFs and two supplied OCR transcripts**. Expectations Investing is shared by two Characters. Every active source is present; file presence does not mean it has been learned.

The owner adopted the seven-source Microstructure sequence: Harris's limited draft excerpts, Johnson and five papers. The two missing books are retained as retired acquisition targets and do not block the revised plan. [ADR-002](../decisions/records/ADR-002-microstructure-reading-scope.md) records this decision. Catalog schema version 2 supports seven Microstructure positions; the other Characters retain four each.

The materials remain in the owner's existing sibling checkout at `../Investing-Books/books`, including its `transcripts/` directory. Set `TRADE_THEORIST_BOOKS_ROOT` to the books directory's absolute path, or pass `--books-root` explicitly. No raw PDFs, transcripts or extracted text are added to the public repository. CI does not require that local directory.

```powershell
$env:TRADE_THEORIST_BOOKS_ROOT = (Resolve-Path ../Investing-Books/books).Path
trade-theorist library report
trade-theorist library verify-files
```

The verification command checks all **32** PDF/transcript sizes and SHA-256 hashes. Transcript records identify their parent PDF hashes and verified sequential page markers. Changed or missing registered files cause a nonzero exit; retired targets are excluded from active verification. Matching fingerprints do not certify coverage, text accuracy, rights or readiness.

`catalog/pilot.json` preserves the earlier publisher candidates and Bogle source used by TASK-004. Use `library report --catalog library/catalog/pilot.json` for that historical scope. `library check` still checks the pilot's publisher URLs; it is not the current local acquisition queue. Regenerate the current readable report with `python scripts/build_inventory_report.py` after reviewing catalog edits.

Before learning, register actual source records and a new Character curriculum version through the learning API. Preserve the completed Bogle artifacts. The supplied transcripts can be loaded privately with `pages_from_transcript`; approved excerpt and paper scopes allow the revised sequence to progress without pretending every source is a full book. See [training sequence](../docs/character-training.md) and the [adopted Microstructure packet](../docs/microstructure-alternatives.md).
