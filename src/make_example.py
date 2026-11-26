"""Generate the static and time-dependent worked examples with verified identities."""

import hashlib
import json
from pathlib import Path
import platform
import sys

from materialization import atf_digest
import reference as ref
import td_example


ROOT = Path(__file__).resolve().parent.parent
SPECIFICATION = "mamut-routing/0.1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    path = ROOT / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return path


def identify(path):
    return dict(path=path.name, sha256=sha(path))


def publish(prefix, manifest, result, checker, backend):
    manifest_path = write(f"{prefix}-instance.manifest.json", manifest)
    evaluation = dict(checker=checker, backend=backend, source_sha256=sha(ROOT / checker),
                      runtime=dict(python=sys.version, platform=platform.platform()),
                      verification_status="incumbent-verified", note="Synthetic specification fixture.")
    display = ref.display_cost(result["cost"])
    standard = dict(specification=manifest["specification"], benchmark_revision=manifest["benchmark_revision"],
                    manifest_sha256=sha(manifest_path), profile=manifest["default_profile"],
                    objective=manifest["objective"], num_routes=result["num_routes"],
                    authoritative_cost=ref.exact_record(result["cost"]),
                    routes_sha256=ref.routes_digest(result["routes"]), evaluation=evaluation,
                    display_overflow=display is None)
    if "route_evaluations" in result:
        standard["route_evaluations"] = result["route_evaluations"]
    write(f"{prefix}-result.json", dict(routes=result["routes"], cost=display, metadata=dict(standard=standard)))


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
    manifest = dict(specification=SPECIFICATION, family="SyntheticExample",
                    benchmark_revision="r1", instance_name="two-customers",
                    problem=problem, objective=objective, default_profile=profile,
                    units=dict(cost="fixture-unit", time="fixture-unit"),
                    instance=identify(instance_path), sidecars=[],
                    materialization=dict(kind="embedded-matrix", interpretation="binary64",
                                         matrix_sha256=ref.matrix_digest(instance["matrix"], "binary64")),
                    features=["single-depot", "homogeneous-capacity", "mandatory-visits", "service-start-windows"])
    publish("example", manifest, result, "src/reference.py", "python-fraction")
    return result


def generate_td():
    sidecar = ROOT / "example-td.atf.json"
    atfs = json.loads(sidecar.read_bytes())
    instance = dict(instance_name=atfs["instance_name"], num_customers=2, depot=0,
                    num_vehicles=2, vehicle_capacity=1, demands=[0, 1, 1], horizon=[0, 15],
                    time_windows=[[0, 15], [6, 7], [7, 9]], service_times=[0, 1, 2], fleet_fixed_cost=1.25,
                    td=dict(model="atf-ndcpwlf", atf_path=sidecar.name, atf_sha256=sha(sidecar)))
    instance_path = write("example-td-instance.json", instance)
    if atfs["horizon"] != instance["horizon"] or atfs["num_customers"] != instance["num_customers"]:
        raise ValueError("the fixture descriptor and ATF header disagree")
    digest = atf_digest(instance["num_customers"] + 1, instance["horizon"], atfs["arcs"])
    manifest = dict(specification=SPECIFICATION, family="SyntheticExample", benchmark_revision="r1",
                    instance_name=instance["instance_name"], problem="TDVRPTW", objective="FleetCostDuration",
                    default_profile="td-binary64-exact-v1", units=dict(cost="fixture-unit", time="fixture-unit"),
                    instance=identify(instance_path), sidecars=[identify(sidecar)],
                    materialization=dict(kind="stored-atf", interpretation="binary64", atf_stream_sha256=digest),
                    features=["single-depot", "homogeneous-capacity", "mandatory-visits", "service-start-windows",
                              "time-dependent-travel", "fixed-vehicle-charge"])
    # Submit in reverse order so the example exercises the serialization order of the witnesses.
    result = td_example.evaluate(instance, atfs, [[2], [1]])
    publish("example-td", manifest, result, "src/td_example.py", "python-fraction-affine-singleton")
    return result


if __name__ == "__main__":
    for result in (generate(), generate_td()):
        print(json.dumps(dict(authoritative_cost=ref.exact_record(result["cost"]),
                              cost=ref.display_cost(result["cost"]), website=ref.display_decimal(result["cost"]))))
