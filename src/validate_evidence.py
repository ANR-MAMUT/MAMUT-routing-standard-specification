#!/usr/bin/env python3
"""Validate s124 evidence integration without rewriting historical provenance records."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path,
                        default=Path("/home/onyr/code/phd/numerical-checker-contracts-investigation"))
    args = parser.parse_args()
    experiment = args.experiment_dir.resolve()
    output = experiment / "newresults/s124-cost-runtime"
    provenance = json.loads((ROOT / "evidence-provenance.json").read_text())
    checks = []

    def check(name, passed):
        checks.append({"check": name, "pass": bool(passed)})

    for relative, digest in provenance["report_source_sha256"].items():
        check("report source: " + relative, sha(ROOT / relative) == digest)
    for relative, digest in provenance["experiment_artifact_sha256"].items():
        check("experiment artifact: " + relative, sha(experiment / relative) == digest)
    recorded_commit = subprocess.check_output(
        ["git", "-C", str(experiment), "rev-parse", provenance["experiment_commit"]], text=True).strip()
    check("experiment commit available", recorded_commit == provenance["experiment_commit"])
    validation = json.loads((output / "validation.json").read_text())
    check("independent numerical replay passed", validation["status"] == "pass" and not validation["mismatches"])
    check("full census validated", validation["instances"] == 296)
    comparison = json.loads((output / "comparison.json").read_text())
    counts = {int(size): item["instances_per_process"] for size, item in comparison["by_size"].items()}
    check("all requested sizes", counts == {100: 56, 400: 60, 600: 60, 800: 60, 1000: 60})
    for size, item in comparison["by_size"].items():
        for scope, variants in item["scopes"].items():
            check(f"all 9 implementations: {size}/{scope}", len(variants) == 9)
    check("generated tables copied exactly", sha(ROOT / "tex/runtime-tables.tex") == sha(output / "runtime-tables.tex"))
    check("generated plot copied exactly", sha(ROOT / "figures/objective-runtime-by-size.pdf") == sha(output / "objective-runtime-by-size.pdf"))
    main_tex = (ROOT / "main.tex").read_text()
    adoption = (ROOT / "tex/adoption.tex").read_text()
    evidence = (ROOT / "tex/evidence.tex").read_text()
    check("evidence follows appendix declaration", main_tex.index("\\appendix") < main_tex.index("\\input{tex/evidence}"))
    check("evidence included once", main_tex.count("\\input{tex/evidence}") == 1)
    check("evidence removed from main body", "\\section{Evidence supporting the design}" not in adoption)
    check("corpus subsection retained", "\\subsection{Corpus and matrix checks}" in evidence)
    check("runtime subsection retained", "\\subsection{Objective-evaluation runtime}" in evidence)
    check("conformance remains in main body", "\\section{Conformance and reproducibility}" in adoption)
    # Preserve the full historical corpus evidence while allowing its new appendix lead-in.
    original = subprocess.check_output(
        ["git", "-C", str(ROOT.parent), "show",
         provenance["report_baseline_commit"] + ":mamut-routing-standard/tex/adoption.tex"], text=True)
    original_corpus = original.split("\\subsection{Objective-evaluation runtime}")[0]
    current_corpus = evidence.split("\\subsection{Objective-evaluation runtime}")[0]
    check("historical corpus evidence preserved", current_corpus.replace("This appendix presents", "This section presents", 1) == original_corpus)
    log = (ROOT / "main.log").read_text()
    check("no unresolved references or citations", not re.search(r"undefined|Rerun to get cross-references right", log, re.I))
    check("no overfull boxes", "Overfull" not in log)
    text = subprocess.check_output(["pdftotext", str(ROOT / "main.pdf"), "-"], text=True)
    check("evidence is Appendix B in PDF", bool(re.search(r"\bB\s+Evidence supporting the design", text)))
    check("complete census in PDF", "296" in text)
    check("no unresolved PDF markers", "??" not in text)
    native = provenance.get("native_extension")
    if native:
        directory = experiment / "newresults/s124-native"
        replay = json.loads((directory / "validation.json").read_text())
        check("native independent replay passed", replay["status"] == "pass" and not replay["mismatches"])
        check("native complete census", replay["instances"] == 296)
        check("native complete timing blocks", replay["timed_blocks"] == 296 * 2 * 15 * 9)
        check("native prior-results preservation", replay["checks"].get("preservation", 0) >= 18)
        check("native boundary suite passed", json.loads((directory / "conformance.json").read_text())["status"] == "pass")
        check("native sanitizer checks passed", json.loads((directory / "build.json").read_text())["selftest"]["status"] == "pass")
        check("native tables copied exactly", sha(ROOT / "tex/native-tables.tex") == sha(directory / "native-tables.tex"))
        for name in ("native-objective-by-size.pdf", "native-checking-by-size.pdf"):
            check("native figure copied exactly: " + name, sha(ROOT / "figures" / name) == sha(directory / name))
        check("native subsection included once", evidence.count("\\input{tex/native-evidence}") == 1)
        check("native appendix reference resolved", bool(re.search(r"\\newlabel\{sec:native-evidence\}\{\{B\.3\}", (ROOT / "main.aux").read_text())))
        actual = subprocess.check_output(["git", "-C", str(experiment), "rev-parse", native["experiment_commit"]], text=True).strip()
        check("native experiment commit available", actual == native["experiment_commit"])
    result = {"status": "pass" if all(c["pass"] for c in checks) else "fail", "checks": checks,
              "checks_passed": sum(c["pass"] for c in checks), "checks_total": len(checks),
              "pdf_sha256": sha(ROOT / "main.pdf"),
              "provenance_sha256": sha(ROOT / "evidence-provenance.json"),
              "validator_sha256": sha(Path(__file__).resolve()),
              "scope": "s124 numerical-evidence integration and current PDF; historical validation/provenance files remain unchanged"}
    (ROOT / "evidence-validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
