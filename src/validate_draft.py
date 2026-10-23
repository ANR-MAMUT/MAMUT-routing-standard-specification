"""Read-only checks of the draft, its synthetic envelope and recorded sources.

Writes validation.json only. Run after building the PDF and recording provenance.
"""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import reference as ref


ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate():
    checks = []

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    provenance = json.loads((ROOT / "provenance.json").read_text())
    for source in provenance["source_files"]:
        check(sha(source["path"]) == source["sha256"], "source identity: " + source["path"])

    main = (ROOT / "main.tex").read_text()
    cff = Path(provenance["author_metadata"]).read_text()
    orcids = re.findall(r"https://orcid.org/([0-9X-]+)", cff)
    check(len(orcids) == 7 and all(value in main for value in orcids), "all 7 author ORCIDs")
    names = re.findall(r"given-names: (.+)\n\s+family-names: (.+)", cff)
    full_names = [first + " " + last for first, last in names]
    positions = [main.index(name) for name in full_names]
    check(len(names) == 7 and positions == sorted(positions), "author citation order")

    tex = "\n".join(p.read_text() for p in ROOT.glob("*.tex"))
    bib = (ROOT / "biblio.bib").read_text()
    cited = set()
    for group in re.findall(r"\\(?:auto|text|paren)cite(?:\[[^]]*\])*\{([^}]+)\}", tex):
        cited.update(group.split(","))
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    check(cited <= keys, "all citation keys present")
    check(len(keys) == len(re.findall(r"@\w+\{", bib)), "unique bibliography keys")
    for path in [*ROOT.glob("*.tex"), *ROOT.glob("*.md"), *ROOT.glob("src/*.py")]:
        check("\u2014" not in path.read_text(), "no em-dash splices: " + path.name)

    for profile in ref.PROFILES:
        check(profile in tex, "documented executable profile: " + profile)
    check("\\lstinputlisting[language=Python]{src/reference.py}" in main, "reference embedded in PDF source")

    manifest_path = ROOT / "example-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    result = json.loads((ROOT / "example-result.json").read_text())
    standard = result["metadata"]["standard"]
    check(sha(manifest_path) == standard["manifest_sha256"], "example manifest identity")
    instance_path = ROOT / manifest["instance"]["path"]
    check(sha(instance_path) == manifest["instance"]["sha256"], "example instance identity")
    check(sha(ROOT / "src/make_example.py") == manifest["generation"]["script_sha256"], "example generator identity")
    instance = ref.load_instance(instance_path.read_text(), standard["profile"], manifest["problem"])
    evaluated = ref.evaluate(instance, result["routes"], standard["objective"])
    check(evaluated["cost"] == ref.read_exact_record(standard["authoritative_cost"]), "example authoritative cost")
    check(evaluated["cost"] == ref.Q(21617278211378381, 36028797018963968), "independent example cost fixture")
    check(result["cost"] == ref.display_cost(evaluated["cost"]), "example compatibility projection")
    check(evaluated["num_routes"] == standard["num_routes"], "example route count")
    check(ref.routes_digest(evaluated["routes"]) == standard["routes_sha256"], "example route-stream identity")
    check(ref.matrix_digest(instance["matrix"], "binary64") == manifest["materialization"]["matrix_sha256"], "example matrix identity")
    check(standard["evaluation"]["source_sha256"] == sha(ROOT / "src/reference.py"), "example checker identity")
    check(standard["assurance"]["proof"] is None, "synthetic example has no proof claim")

    log = (ROOT / "main.log").read_text()
    check("Output written on main.pdf" in log, "PDF build completed")
    for pattern in (r"^!", "undefined references", "Citation .* undefined", "Overfull", "Infinite glue"):
        check(re.search(pattern, log, re.MULTILINE) is None, "no LaTeX diagnostic: " + pattern)
    check("WARN" not in (ROOT / "main.blg").read_text(), "no biber warnings")
    pdf_text = subprocess.run(["pdftotext", str(ROOT / "main.pdf"), "-"],
                              check=True, capture_output=True, text=True).stdout
    check("??" not in pdf_text, "no unresolved PDF references")
    check(all(oid in pdf_text for oid in orcids), "ORCIDs appear in compiled PDF")
    check("binary64-exact-v1" in pdf_text and "decimal-grid-3-v1" in pdf_text, "profile identifiers appear in PDF")
    tests_log = ROOT / "conformance-tests.log"
    tests_text = tests_log.read_text()
    check("Ran 24 tests" in tests_text and tests_text.rstrip().endswith("OK"), "24 conformance tests passed")

    artifacts = [p for p in ROOT.rglob("*") if p.is_file() and
                 (p.suffix in (".tex", ".bib", ".md", ".py") or
                  p.name in ("main.pdf", "provenance.json", "example-instance.json",
                             "example-manifest.json", "example-result.json")) and p.name != "biblio-clean.bib"]
    output = dict(status="passed", check_count=len(checks), checks=checks,
                  python=sys.version, artifacts={str(p.relative_to(ROOT)): sha(p) for p in sorted(artifacts)},
                  conformance_tests=dict(count=24, result="passed", evidence=tests_log.name,
                                         sha256=sha(tests_log), command="python -m unittest discover -s src -v"),
                  limitations=["Synthetic/reference verification, not production conformance certification",
                               "No full-corpus audit or timing experiment rerun in s121",
                               "No cross-platform certification or optimality proof"])
    (ROOT / "validation.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(dict(status="passed", check_count=len(checks), artifacts=len(artifacts))))


if __name__ == "__main__":
    validate()
