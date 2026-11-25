# MAMUT-routing standard specification

The [specification PDF](main.pdf), version 0.1, follows a submitted set of routes from the published instance to its exact result. Static and time-dependent (TD) routing use the same binary64 input convention. A static instance supplies a matrix, while a TD instance supplies directed arrival-time functions and requires a scheduling decision for each route. In both cases a materializer can regenerate the published arc values from pinned inputs and code. The complete semantic digest verifies their equivalence.

## Read the standard

The [introduction](tex/foundations.tex) distinguishes conformance, mathematical fidelity and reproducibility. It explains the difference between a JSON token's decimal value, its binary64 reading and the value passed to exact arithmetic. The [instance section](tex/instance-materialization.tex) identifies the files, code and digests needed to reproduce that reading.

The [shared route calculation](tex/evaluation.tex) follows a vehicle from depot departure to depot return. The [TD scheduling rules](tex/td-core.tex) show how to minimize elapsed time and choose the earliest departure when several departures attain the same minimum. The [result section](tex/results.tex) uses two worked examples to explain what a checker stores and what a website displays.

- The [static instance](example-instance.json), [manifest](example-instance.manifest.json) and [result](example-result.json) show the exact sum of three binary64 arc costs that displays as `0.6`.
- The [TD instance](example-td-instance.json), [arc functions](example-td.atf.json), [manifest](example-td-instance.manifest.json) and [result](example-td-result.json) show how to read the exact duration and earliest departure of each stored route. The exact solution total, including two vehicle charges, is `79/6`.

After the bibliography, the appendices provide [mathematical notation](tex/notation.tex), [canonical digest encodings](tex/materialization-format.tex) with [byte-level examples](materialization-vectors.json), the [Python and native implementation guide](tex/implementation-guide.tex), [alternative input readings and arithmetic modes](tex/alternative-readings.tex), the [existence proof for TD route minima](tex/td-attainment.tex), a [worked departure at a jump](tex/td-jump.tex), [solver self-reports](tex/solver-claim.tex) and the [certification order of an edition and a result](tex/certification-order.tex).

## Build and check

Use an environment with Python, pdfLaTeX, biblatex/biber and latexmk. From the repository root run

```bash
python -m unittest discover -s src -v
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
python src/validate_document.py
```

The [static reference](src/reference.py) implements the exact and alternative static readings. The [TD example checker](src/td_example.py) covers the affine single-customer routes of the worked example. The [example generator](src/make_example.py) writes the synthetic results and identifies the runtime and source that produced them. The [document validator](src/validate_document.py) checks the built PDF, the bibliography and the worked examples. The origin of this repository is recorded in [HISTORY.md](HISTORY.md).

## Licence

The text of the specification (`main.tex`, `tex/`, `figures/` and the compiled PDF) is licensed under [CC BY 4.0](LICENSE).
