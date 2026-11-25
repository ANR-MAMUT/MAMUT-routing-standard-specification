"""Read-only checks of the built document and its worked examples.

Run from the repository root after building main.pdf. The script reads only files of this repository and prints a summary.
"""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

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

    main = (ROOT / "main.tex").read_text()
    tex = "\n".join(p.read_text() for p in (ROOT / "tex").glob("*.tex"))
    bib = (ROOT / "biblio.bib").read_text()
    cited = set()
    for group in re.findall(r"\\(?:auto|text|paren)cite(?:\[[^]]*\])*\{([^}]+)\}", tex):
        cited.update(group.split(","))
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    check(cited <= keys, "all citation keys present")
    check(len(keys) == len(re.findall(r"@\w+\{", bib)), "unique bibliography keys")
    for path in [*(ROOT / "tex").glob("*.tex"), *ROOT.glob("*.md"), *ROOT.glob("src/*.py")]:
        check("\u2014" not in path.read_text(), "no em-dash splices: " + path.name)

    for profile in ref.PROFILES:
        check(profile in tex, "documented executable profile: " + profile)
    check((ROOT / "src/reference.py").is_file() and "\\input{tex/td-core}" in main
          and "\\lstinputlisting" not in main + tex, "TD core and separate static code companion")

    manifest_path = ROOT / "example-instance.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    result = json.loads((ROOT / "example-result.json").read_text())
    standard = result["metadata"]["standard"]
    check(sha(manifest_path) == standard["manifest_sha256"], "example manifest identity")
    instance_path = ROOT / manifest["instance"]["path"]
    check(sha(instance_path) == manifest["instance"]["sha256"], "example instance identity")
    check("generation" not in manifest, "generation history is separate from the instance manifest")
    check(manifest["default_profile"] == standard["profile"], "example uses manifest default profile")
    check(manifest["materialization"]["kind"] == "embedded-matrix", "example matrix representation")
    instance = ref.load_instance(instance_path.read_text(), standard["profile"], manifest["problem"])
    evaluated = ref.evaluate(instance, result["routes"], standard["objective"])
    check(evaluated["cost"] == ref.read_exact_record(standard["authoritative_cost"]), "example authoritative cost")
    check(evaluated["cost"] == ref.Q(21617278211378381, 36028797018963968), "independent example cost fixture")
    check(result["cost"] == ref.display_cost(evaluated["cost"]), "example compatibility projection")
    check(evaluated["num_routes"] == standard["num_routes"], "example route count")
    check(ref.routes_digest(evaluated["routes"]) == standard["routes_sha256"], "example route-stream identity")
    check(ref.matrix_digest(instance["matrix"], "binary64") == manifest["materialization"]["matrix_sha256"], "example matrix identity")
    check(standard["evaluation"]["source_sha256"] == sha(ROOT / "src/reference.py"), "example checker identity")
    check("optimality" not in result["metadata"], "synthetic example has no optimality claim")
    check(standard["evaluation"]["verification_status"] == "incumbent-verified",
          "synthetic example records incumbent verification separately")

    log = (ROOT / "main.log").read_text()
    check("Output written on main.pdf" in log, "PDF build completed")
    for pattern in (r"^!", "undefined references", "Citation .* undefined", "Overfull", "Infinite glue"):
        check(re.search(pattern, log, re.MULTILINE) is None, "no LaTeX diagnostic: " + pattern)
    check("WARN" not in (ROOT / "main.blg").read_text(), "no biber warnings")
    if shutil.which("pdftotext"):
        pdf_text = subprocess.run(["pdftotext", str(ROOT / "main.pdf"), "-"],
                                  check=True, capture_output=True, text=True).stdout
        check("??" not in pdf_text, "no unresolved PDF references")
        check("binary64-exact-v1" in pdf_text and "decimal-grid-3-v1" in pdf_text, "profile identifiers appear in PDF")
    print(json.dumps(dict(status="passed", check_count=len(checks))))


if __name__ == "__main__":
    validate()
