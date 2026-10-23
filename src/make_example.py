"""Generate a synthetic, fully identified result for the specification draft."""

import hashlib
import json
from pathlib import Path
import platform
import sys

import reference as ref


ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    path = ROOT / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return path


def generate():
    profile = "binary64-exact-v1"
    problem = "VRPTW"
    objective = "MonoCost"
    raw = dict(num_customers=2, depot=0, num_vehicles=None, vehicle_capacity=2,
               demands=[0, 1, 1], arc_costs=[[0, 0.1, 0.3], [0.1, 0, 0.2], [0.3, 0.2, 0]],
               time_windows=[[0, 10], [0, 10], [0, 10]], service_times=[0, 0, 0])
    instance_path = write("example-instance.json", raw)
    instance = ref.load_instance(instance_path.read_text(), profile, problem)
    result = ref.evaluate(instance, [[1, 2]], objective)
    manifest = dict(specification="mamut-static/0.1-draft", family="SyntheticExample",
                    benchmark_revision="synthetic-v1", instance_name="two-customers",
                    problem=problem, objective=objective, profile=profile,
                    units=dict(cost="fixture-unit", time="fixture-unit"),
                    cost_is_travel_time=True,
                    instance=dict(path=instance_path.name, sha256=sha(instance_path)),
                    sidecars=[],
                    materialization=dict(recipe="embedded-matrix", interpretation="binary64",
                                         matrix_sha256=ref.matrix_digest(instance["matrix"], "binary64")),
                    generation=dict(recipe="synthetic literal fixture", script="src/make_example.py",
                                    script_sha256=sha(ROOT / "src/make_example.py"), seed=None),
                    features=["single-depot", "homogeneous-capacity", "mandatory-visits", "service-start-windows"])
    manifest_path = write("example-manifest.json", manifest)
    standard = dict(specification="mamut-static/0.1-draft", benchmark_revision="synthetic-v1",
                    manifest_sha256=sha(manifest_path), profile=profile, objective=objective,
                    num_routes=result["num_routes"], authoritative_cost=ref.exact_record(result["cost"]),
                    routes_sha256=ref.routes_digest(result["routes"]),
                    evaluation=dict(checker="src/reference.py", source_sha256=sha(ROOT / "src/reference.py"),
                                    runtime=dict(python=sys.version, platform=platform.platform()),
                                    verification_status="evaluated-by-reference"),
                    display_overflow=ref.display_cost(result["cost"]) is None,
                    assurance=dict(incumbent_verification="checked-by-reference",
                                   source_reported_claim=None,
                                   solver=dict(name=None, version=None, search_arithmetic=None, tolerances=None),
                                   lower_bound=None, proof=None,
                                   note="Synthetic specification fixture. No solver run or optimality claim."))
    write("example-result.json", dict(routes=result["routes"], cost=ref.display_cost(result["cost"]),
                                      metadata=dict(standard=standard)))
    return result


if __name__ == "__main__":
    result = generate()
    print(json.dumps(dict(authoritative_cost=ref.exact_record(result["cost"]),
                          cost=ref.display_cost(result["cost"]), website=ref.display_decimal(result["cost"]))))
