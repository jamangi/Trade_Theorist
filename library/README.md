# Library

The [current inventory](catalog/INVENTORY_REPORT.md) covers all seven Characters and their 28 ordered slots. Its [machine-readable catalog](catalog/characters.json) records 25 local PDFs, two missing titles, actual edition evidence and preparation gaps. Expectations Investing is shared by two Characters. File presence does not mean a book is complete or learned.

The owner supplied an existing sibling checkout at `../Investing-Books/books`. The PDFs remain there; no copies or extracts are added to the public repository. Set `TRADE_THEORIST_BOOKS_ROOT` to that directory's absolute path, or pass `--books-root` explicitly. Nothing depends on a hardcoded username or another repository being present in CI.

```powershell
$env:TRADE_THEORIST_BOOKS_ROOT = (Resolve-Path ../Investing-Books/books).Path
trade-theorist library report
trade-theorist library verify-files
```

The verification command checks sizes and SHA-256 hashes without extracting or publishing content. It does not modify files, grant rights or promote learning readiness. Known unacquired titles are reported separately from changed or missing previously registered files.

`catalog/pilot.json` preserves the earlier publisher candidates and the registered Bogle source used by TASK-004. Use `library report --catalog library/catalog/pilot.json` to inspect that historical scope. `library check` still checks the pilot's publisher URLs; it cannot verify local books. Regenerate the current readable report with `python scripts/build_inventory_report.py` after editing and reviewing catalog metadata.

Before learning, register actual edition-specific source records and a new curriculum version through the learning API. Preserve the completed Bogle artifacts. See [training sequence](../docs/character-training.md) and [microstructure alternatives](../docs/microstructure-alternatives.md).
