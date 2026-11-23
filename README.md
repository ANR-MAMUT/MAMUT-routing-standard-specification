# MAMUT-routing standard specification

The [review PDF](main.pdf) follows a static or time-dependent instance from its materialized binary64 inputs to a checked result. The two default profiles are `binary64-exact-v1` and `td-binary64-exact-v1`. Both use exact evaluation and a nearest-binary64 display projection. The draft targets MAMUT-routing-lib v0.13. The repository is private for coauthor review. The project has yet to select a license for the standalone specification.

## Worked examples

- The [static instance](example-instance.json), [manifest](example-manifest.json) and [result](example-result.json) show how three binary64 arc costs sum to an exact fraction that displays as `0.6`.
- The [TD instance](example-td-instance.json), [arc functions](example-td.atf.json), [manifest](example-td-manifest.json) and [result](example-td-result.json) show two routes with a fixed vehicle charge. Each route has an exact duration and earliest departure in stored route order.
- The [digest vectors](materialization-vectors.json) give reproducible examples of the matrix and ATF stream encodings.

The [LaTeX entry point](main.tex) lists the sections in reading order. Appendices specify the semantic digest byte streams, list alternative readings and historical folds, explain the optional solver self-report and prove that the earliest TD minimizer exists.

## Build and check

Use an environment with Python, pdfLaTeX, biblatex/biber and latexmk. On Onyr's Nix setup, enter `nix develop base`. Run the following from the repository root.

```bash
python -m unittest discover -s src -v
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The [example generator](src/make_example.py) writes the synthetic manifests and results, including their file hashes and evaluator identity. The [static companion](src/reference.py) implements the static reference and alternative readings. The TD worked example covers its stated fixture. Earlier review snapshots and their provenance are described in [HISTORY.md](HISTORY.md).
