# MAMUT-routing standard specification

Review draft 0.1 specifies static CVRP/VRPTW numerical semantics before production implementation or BKS migration. Read [main.pdf](main.pdf), built from [main.tex](main.tex). The 7 authors and ORCID identifiers follow the MAMUT-routing project's `CITATION.cff` in the recorded source snapshot. This draft does not represent approval by every listed author.

This repository is initially private for review. Public release, integration as a MAMUT-routing submodule and presentation in the website documentation are deferred. [HISTORY.md](HISTORY.md) records extraction of the original directory history and preservation of the current worktree. A license has not been selected for this standalone repository.

The draft separates generation, instance interpretation, evaluation and result semantics. Onyr confirmed during s121 that the first standard is static, retains binary64 interpretation after generation or rederivation, and uses exact evaluation of those binary64 values by default for Poryos/Mamut as well as SINTEF-derived fractional matrices. DIMACS/ORTEC use an equivalent integer specialization where all interpreted quantities are integral. Decimal and decimal-grid interpretations remain separately identified alternatives. These latest decisions supersede the earlier proposed decimal-grid defaults for Poryos/Mamut.

The top-level BKS `cost` remains a compatibility projection. Authoritative cost and profile identity belong in metadata. The draft also defines temporal feasibility, lexicographic objectives, result provenance and proof-assurance distinctions. Matrix digests, metadata names, display rounding, depot initialization and adoption arrangements are explicit draft proposals. The open-problems section distinguishes these from the decisions already settled in conversation.

The inventory, numerical comparisons and objective-evaluation measurements are presented as results of this document. Local investigation pointers remain in LaTeX comments rather than public-facing prose or bibliography entries. Onyr confirmed on 26 October that v0.13 will implement the complete static specification, with breaking changes from v0.12 accepted during the standard's early development. The release-scope item remains visible among the open decisions, recording the confirmed policy and pending implementation/release obligations.

## Files

- [tex/foundations.tex](tex/foundations.tex): scope, binary64 and JSON, the 4 contract stages.
- [tex/contracts.tex](tex/contracts.tex): the 1,976-instance static inventory, generation/materialization and core input semantics.
- [tex/evaluation.tex](tex/evaluation.tex): integrated profiles, family defaults, exact/rounded algorithms and equivalent integer implementations.
- [tex/results.tex](tex/results.tex): authoritative metadata, BKS ranking, display, solver and proof claims.
- [tex/adoption.tex](tex/adoption.tex): existing evidence, conformance, migration and open decisions.
- [main.tex](main.tex): document entry point and shared preamble.
- [src/reference.py](src/reference.py): standalone standard-library numerical reference, also embedded in the PDF appendix.
- [src/test_reference.py](src/test_reference.py): 24 boundary and conformance tests.
- [src/make_example.py](src/make_example.py): creates the synthetic instance, manifest and result with actual hashes.
- [src/validate_draft.py](src/validate_draft.py): checks the compiled document, recorded sources and synthetic result.
- [provenance.json](provenance.json): source paths, revisions, decision inputs and source-file hashes.
- [validation.json](validation.json): document and companion checks recorded for the earlier s121 snapshot.
- [migration-validation.json](migration-validation.json): focused source-transfer, history, numerical-reference and standalone-build verification for the repository migration.

The reference consumes materialized instances using the existing static field names, plus explicit profile/problem/objective arguments. It is not a production sidecar loader, BKS migration, complete historical-release emulator or validator for the proposed provenance envelope. Error ordering is unspecified. Current family audits and runtime measurements are cited as existing evidence rather than rerun experiments.

## Build and check

From the repository root, run the following commands in an environment providing Python, pdfLaTeX, biblatex/biber, latexmk and Poppler's `pdftotext`:

```bash
python -m unittest discover -s src -v
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

On Onyr's Nix setup, `nix develop base` provides the required tools. The source build and numerical tests do not depend on the former report checkout. The PDF is versioned for private review. Rebuild it when its sources change.

`python src/make_example.py` regenerates the synthetic artifacts and their hashes when an intentional example update is needed. This is not required for reading, testing or building the unchanged draft.

`provenance.json` records consulted Worklog snapshots, source hashes and audit revisions. `src/validate_draft.py` is the historical full provenance validator, requires the recorded external paths and build/test logs, and writes `validation.json` on success. It currently stops on pre-existing Worklog source-hash mismatches. The historical `validation.json`, `link-validation.json` and `editorial-validation.json` retain their original scope and identities. They are not silently replaced by migration checks. Portable archival verification of those external sources remains a follow-up before public release.
