"""Reproduce the TD appendix tables from a restored routing-numerical-contracts archive."""

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from statistics import median


# Manifest hashes at 0nyr/routing-numerical-contracts 75905c8.
INPUT_HASHES = {
    "original-inputs": "71c6a8d31dcdcd9f5010bcb0b407c84dd4e55544a45b0295619a5a9377b37d6d",
    "rational-panel": "5429feff33496a2d043d43010a2fc21d8d2644bca791ffcd93e68a56ceb1c9af",
}
RESULT_HASHES = {
    "original-inputs": "3fe770dfabb6a2a22851d30564cce26bc3c4c8c033289df0babb52186db2db52",
    "rational-panel": "6a46750dde57208e5390af125f77c337ba7df7112fa6554bdf6d0d3eff26fc9d",
}
TIMING_HASH = "aa333a241e5d3e31c1229f92adbb5048ac1699fd3fb5536d64f98f118d5fe5bd"
RELEASES = ("v011", "v012")


def read_pinned(path, digest):
    data = path.read_bytes()
    if sha256(data).hexdigest() != digest:
        raise ValueError(f"Unexpected content in {path}")
    return json.loads(data)


def agreement(root, panel):
    inputs = read_pinned(root / "manifests" / f"{panel}.json", INPUT_HASHES[panel])
    by_id = {entry["id"]: entry for entry in inputs}
    results = read_pinned(root / "results" / f"{panel}.json", RESULT_HASHES[panel])
    counts = Counter()
    for entry in results:
        result = read_pinned(root / entry["result"], entry["sha256"])
        source = by_id[result["id"]]
        if result["input_sha256"] != source["sha256"]:
            raise ValueError(f"Different materialized input for {result['id']}")
        record = read_pinned(root / source["cache"], source["sha256"])
        solution = result["current"]
        routes = solution["routes"]
        if solution["structural_errors"] or sorted(r["route"] for r in routes) != sorted(record["bks"]["routes"]):
            raise ValueError(f"Invalid or mismatched routes for {result['id']}")
        cost = Fraction()
        for route in routes:
            exact = route["exact"]["binary"]
            if not (exact["feasible"] and exact["attained"]):
                raise ValueError(f"Missing feasible optimum for {result['id']}")
            duration = Fraction(exact["duration"])
            cost += duration
            for version in RELEASES:
                fold = route["folds"][version]
                counts["duration matches", version] += fold["duration"] == float(duration)
                counts["infeasible departures", version] += not fold["binary_feasible_at_departure"]
        objective = record["bks"]["objective_function"]
        if objective == "FleetCostDuration":
            cost += len(routes) * Fraction(float(record["instance"]["fleet_fixed_cost"]))
        elif objective != "Duration":
            raise ValueError(f"Unknown objective {objective}")
        for version in RELEASES:
            counts["solution matches", version] += solution["totals"][version]["cost"] == float(cost)
        counts["routes"] += len(routes)
    print(f"{panel}: {len(results)} solutions, {counts['routes']} routes")
    for metric in ("duration matches", "infeasible departures", "solution matches"):
        print(f"  {metric} (v0.11, v0.12):", *(counts[metric, v] for v in RELEASES))


def route_key(row):
    return row["panel"], row["id"], row["route_index"]


def timings(root):
    data = read_pinned(root / "results/controlled-td.json", TIMING_HASH)
    folds = {route_key(row): row["median_seconds"] for row in data["routes"]}
    rows = []
    for row in data["rational"]:
        if row["status"] != "complete":
            raise ValueError(f"Incomplete timing for {route_key(row)}")
        pair = folds[route_key(row)]
        rows.append((row["panel"], pair["v011"], pair["v012"], median(row["samples"]["binary"])))
    for panel in ("original", "broader", "combined"):
        subset = [r for r in rows if panel == "combined" or r[0] == panel]
        times = [1000 * median(r[i] for r in subset) for i in (1, 2, 3)]
        ratios = [median(r[3] / r[i] for r in subset) for i in (1, 2)]
        print(f"{panel}, {len(subset)} routes (ms):", *(f"{t:.3f}" for t in times))
        print("  paired ratios (exact/v0.11, exact/v0.12):", *(f"{r:.1f}" for r in ratios))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="checkout with the study's restored input and result bundles")
    root = parser.parse_args().archive
    for name in INPUT_HASHES:
        agreement(root, name)
    timings(root)
