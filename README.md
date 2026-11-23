# MAMUT-routing standard specification

The 20 November review draft covers static CVRP/VRPTW and the common TD route and result contracts. The 7 authors and ORCID identifiers follow the MAMUT-routing project citation metadata. Coauthor review is pending. [Review PDF](main.pdf) · [LaTeX entry point](main.tex)

The draft separates generation, instance interpretation, evaluation and result semantics. Materialization fixes the binary64 matrix entries or ATF knots. The default checker evaluates those values exactly. Eligible integer static families admit equivalent integer evaluation. Static decimal and grid alternatives have separate identities. In TD routing, the authoritative departure is the smallest one attaining the minimum route duration.

The top-level BKS `cost` remains a compatibility projection. Authoritative cost and profile identity belong in metadata. The draft also defines temporal feasibility, lexicographic objectives, result provenance and proof-assurance distinctions. Only customers receive service. All profiles require zero depot service. The draft also specifies matrix digests, display rounding and proposed metadata names. The open-problems section distinguishes these from the decisions already settled in conversation.

The inventory, numerical comparisons and objective-evaluation measurements are presented as results of this document. Local investigation pointers remain in LaTeX comments rather than public-facing prose or bibliography entries. Onyr confirmed on 26 October that v0.13 will implement the static specification, with breaking changes from v0.12 accepted during the standard's early development. The 5 November scope decision also includes TD. Family materialization annexes, conformance and production implementation remain open.

Profiles retain their individual `-v1` contract revisions so that a specific profile can evolve without silently changing an existing identifier. Routing notation follows the shared manuscript conventions for the solution set, route vectors, vertex/customer sets and instance attributes. Submitted route order is recorded separately from the mathematical solution set. The numerical-domain notation and the stored single-depot indexing remain local to this specification.

This repository is initially private for review. Public release, integration as a MAMUT-routing submodule and presentation in the website documentation are deferred. [HISTORY.md](HISTORY.md) records extraction of the original directory history and preservation of the current worktree. A license has not been selected for this standalone repository.

## Files

- [tex/foundations.tex](tex/foundations.tex): scope, binary64 and JSON, the 4 contract stages.
- [tex/contracts.tex](tex/contracts.tex): the 1,976-instance static inventory, generation/materialization and core input semantics.
- [tex/evaluation.tex](tex/evaluation.tex): integrated profiles, family defaults, exact/rounded algorithms and equivalent integer implementations.
- [tex/td-core.tex](tex/td-core.tex) introduces arrival functions, exact timing and departure optimization, with an example from Blauth-Nairobi.
- [tex/td-attainment.tex](tex/td-attainment.tex) proves existence and rationality of the earliest duration minimizer.
- [tex/static-rounded.tex](tex/static-rounded.tex) gives the operational static alternatives in an appendix.
- [tex/results.tex](tex/results.tex): authoritative metadata, BKS ranking, display, solver and proof claims.
- [tex/adoption.tex](tex/adoption.tex): conformance, migration and open decisions.
- [Appendix B](tex/evidence.tex) compares historical static rankings in [317 candidate pairs](tex/static-history.tex), checks the SINTEF matrices and gives the objective-runtime census on 296 instances.
- [Appendix D](tex/td-evidence.tex) compares the released TD folds with the proposed exact profile using the Rifki-30 jump and archived routes. The [native scheduling study](tex/td-native.tex) compares exact prefix composition and a departure sweep. The [Kayros pilot](tex/td-kayros.tex) reports full-instance timings and checks the actual Kayros root multipliers against every feasible route on Rifki-1 and Rifki-13.
- To reproduce the new static comparison, run `python src/check_static_history.py /path/to/data/static-history.json.gz` on the [pinned study archive](https://github.com/0nyr/routing-numerical-contracts/tree/75905c8827f959621ea808894e28136d248d2d15). After restoring its input and result bundles as described in the study README, run `python src/summarize_td_panels.py /path/to/routing-numerical-contracts` to reproduce both TD tables. The [figure generator](src/plot_rifki_jump.py) takes the same archive's `fixtures/rifki30-route.json` and uses Matplotlib.
- [tex/runtime-tables.tex](tex/runtime-tables.tex): generated per-size timing and preparation tables for all 9 measured implementations.
- [figures/objective-runtime-by-size.pdf](figures/objective-runtime-by-size.pdf): standalone runtime plot for both measurement scopes.
- [tex/native-evidence.tex](tex/native-evidence.tex) and [tex/native-tables.tex](tex/native-tables.tex): native C++/pybind11 range/conformance evidence, complete solution checking and Python integration measurements.
- [figures/native-objective-by-size.pdf](figures/native-objective-by-size.pdf) and [figures/native-checking-by-size.pdf](figures/native-checking-by-size.pdf): native objective and full-check/integration plots, alongside preserved Python context.
- [tex/notation.tex](tex/notation.tex): mathematical domains, parsing/rounding operators, a worked binary64-to-rational example and the appendix table of symbols.
- [main.tex](main.tex): document entry point and shared preamble.
- [src/reference.py](src/reference.py): standalone standard-library reference for the static profiles, distributed alongside the document.
- [src/test_reference.py](src/test_reference.py): 24 boundary and conformance tests.
- [src/make_example.py](src/make_example.py): creates the synthetic instance, manifest and result with actual hashes.
- [src/validate_draft.py](src/validate_draft.py): checks the compiled document, recorded sources and synthetic result.
- [src/validate_evidence.py](src/validate_evidence.py) verifies the census exports, appendix and PDF against the frozen October s124 snapshot.
- [evidence-provenance.json](evidence-provenance.json) and [evidence-validation.json](evidence-validation.json): s124 experiment identities, export hashes and report-integration checks.
- [provenance.json](provenance.json): source paths, revisions, decision inputs and source-file hashes.
- [validation.json](validation.json): document and companion checks recorded for the earlier s121 snapshot.

- [migration-validation.json](migration-validation.json) records the October extraction checks.

## Build and check

From the repository root, run the following commands in an environment providing Python, pdfLaTeX, biblatex/biber, latexmk and Poppler's `pdftotext`:

```bash
python -m unittest discover -s src -v
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

On Onyr's Nix setup, `nix develop base` provides the required tools. The source build and numerical tests do not depend on the former report checkout. The PDF is versioned for private review. Rebuild it when its sources change.

`python src/make_example.py` regenerates the synthetic artifacts and their hashes when an intentional example update is needed. This is not required for reading, testing or building the unchanged draft.

`provenance.json` records consulted Worklog snapshots, source hashes and audit revisions. `src/validate_draft.py` is the historical full provenance validator, requires the recorded external paths and build/test logs, and writes `validation.json` on success. It currently stops on pre-existing Worklog source-hash mismatches. The historical `validation.json`, `link-validation.json` and `editorial-validation.json` retain their original scope and identities. They are not silently replaced by migration checks. Portable archival verification of those external sources remains a follow-up before public release.
