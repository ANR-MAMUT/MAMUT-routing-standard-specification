# MAMUT-routing standard specification

Review draft 0.1 specifies static CVRP/VRPTW numerical semantics before production implementation or BKS migration. Read [main.pdf](main.pdf), built from [main.tex](main.tex). The 7 authors and ORCID identifiers follow the MAMUT-routing project's `CITATION.cff` in the recorded source snapshot. This draft does not represent approval by every listed author.

The draft separates generation, instance interpretation, evaluation and result semantics. Onyr confirmed during s121 that the first standard is static, retains binary64 interpretation after generation or rederivation, and uses exact evaluation of those binary64 values by default for Poryos/Mamut as well as SINTEF-derived fractional matrices. DIMACS/ORTEC use an equivalent integer specialization where all interpreted quantities are integral. Decimal and decimal-grid interpretations remain separately identified alternatives. These latest decisions supersede the earlier proposed decimal-grid defaults for Poryos/Mamut.

The top-level BKS `cost` remains a compatibility projection. Authoritative cost and profile identity belong in metadata. The draft also defines temporal feasibility, lexicographic objectives, result provenance and proof-assurance distinctions. Matrix digests, metadata names, display rounding, depot initialization and adoption arrangements are explicit draft proposals. The open-problems section distinguishes these from the decisions already settled in conversation.

## Files

- [foundations.tex](foundations.tex): scope, binary64 and JSON, the 4 contract stages.
- [contracts.tex](contracts.tex): the 1,976-instance static inventory, generation/materialization and core input semantics.
- [evaluation.tex](evaluation.tex): integrated profiles, family defaults, exact/rounded algorithms and equivalent integer implementations.
- [results.tex](results.tex): authoritative metadata, BKS ranking, display, solver and proof claims.
- [adoption.tex](adoption.tex): existing evidence, conformance, migration and open decisions.
- [src/reference.py](src/reference.py): standalone standard-library numerical reference, also embedded in the PDF appendix.
- [src/test_reference.py](src/test_reference.py): 24 boundary and conformance tests.
- [src/make_example.py](src/make_example.py): creates the synthetic instance, manifest and result with actual hashes.
- [src/validate_draft.py](src/validate_draft.py): checks the compiled document, recorded sources and synthetic result.
- [provenance.json](provenance.json): source paths, revisions, decision inputs and source-file hashes.
- [validation.json](validation.json): completed document and companion checks for this working snapshot.

The reference consumes materialized instances using the existing static field names, plus explicit profile/problem/objective arguments. It is not a production sidecar loader, BKS migration, complete historical-release emulator or validator for the proposed provenance envelope. Error ordering is unspecified. Current family audits and runtime measurements are cited as existing evidence rather than rerun experiments.

## Build and check

From `/home/onyr/code/phd/report`, use the existing project dev shell:

```bash
nix develop path:./nix-dev -c bash -c 'cd mamut-routing-standard && python -m unittest discover -s src -v > conformance-tests.log 2>&1'
nix develop path:./nix-dev -c bash -c 'cd mamut-routing-standard && python src/make_example.py'
nix develop path:./nix-dev -c bash -c 'cd mamut-routing-standard && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex'
nix develop path:./nix-dev -c bash -c 'cd mamut-routing-standard && python src/validate_draft.py'
```

Build with pdfLaTeX and biblatex/biber. `provenance.json` records the consulted Worklog snapshots, source hashes and audit revisions. The recorded source paths remain external dependencies of the provenance check. The first draft is versioned in this repository. The session log is `/home/onyr/code/phd/tdvrptw-workspace/reports/sessions/2026-10-23-session-121.md`.
