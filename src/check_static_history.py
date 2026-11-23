"""Reproduce the static candidate rankings from the frozen numerical study."""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import chain, combinations
import json
from pathlib import Path


# 0nyr/routing-numerical-contracts, commit 75905c8827f959621ea808894e28136d248d2d15
ARCHIVE_SHA256 = "5d4d0617d6796d954aaf56c8c978bca7cd4fb58b005d8d7e8f68c00619a2536c"
MANILA = (
    "benchmarks/Mamut2026/CVRP/fastest/manila/n=221/mamut-manila-n221-k48-hyb/"
    "mamut-manila-n221-k48-hyb.bks.MonoCost.json"
)
EXPECTED = {(-1, -1, -1): 286, (1, 0, -1): 3, (1, 0, 0): 22, (1, 0, 1): 6}


def objective_keys(instance, candidate):
    flat = 0.0
    decimal = Fraction()
    binary = Fraction()
    for arc in chain.from_iterable(candidate["vectors"]):
        value = float(arc)
        flat += value
        decimal += Fraction(str(arc))
        binary += Fraction(value)
        if instance["family"] == "Dimacs2021" and not value.is_integer():
            raise ValueError(f"Nonintegral Dimacs2021 arc in {instance['id']}")

    costs = (flat, decimal, binary)
    stored = (candidate["flat"], Fraction(candidate["decimal"]), Fraction(candidate["binary"]))
    if costs != stored:
        raise ValueError(f"Recomputed costs differ from the archive for {instance['id']}")
    if instance["objective"] == "MonoCost":
        return tuple((cost,) for cost in costs)
    if instance["objective"] == "HierarchicalVehicleCost":
        return tuple((candidate["num_routes"], cost) for cost in costs)
    raise ValueError(f"Unknown objective {instance['objective']}")


def check_history(path):
    archive = path.read_bytes()
    if hashlib.sha256(archive).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Checksum mismatch for the frozen static-history.json.gz")
    instances = json.loads(gzip.decompress(archive))
    counts = Counter()
    candidate_count = 0
    manila_checked = False
    for instance in instances:
        candidates = instance["candidates"]
        candidate_count += len(candidates)
        if len(candidates) < 2:
            continue
        # The archive lists distinct candidates in reverse chronological order.
        keys = [objective_keys(instance, candidate) for candidate in candidates]
        for later, earlier in combinations(keys, 2):
            signs = tuple((a > b) - (a < b) for a, b in zip(later, earlier))
            counts[signs] += 1
            if instance["id"] == MANILA:
                a, b = later[2][-1], earlier[2][-1]
                if b - a != Fraction(5, 2**47) or (float(a), float(b)) != (47689.131, 47689.131):
                    raise ValueError("Manila exact difference or rounded display differs")
                manila_checked = True
    if (len(instances), candidate_count) != (1956, 2273) or counts != EXPECTED or not manila_checked:
        raise ValueError(f"Unexpected corpus, rankings or Manila witness: {counts}")

    print(f"{len(instances)} instances, {candidate_count} candidates, {sum(counts.values())} pairs")
    print("Later candidate versus predecessor (v0.11, v0.12, proposed exact binary64)")
    direction = {-1: "better", 0: "tied", 1: "worse"}
    for signs, count in sorted(counts.items()):
        print(f"{', '.join(direction[x] for x in signs)}: {count}")
    print("The later Manila candidate costs 5/2^47 s less. Both displays are 47689.131 s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="path to the pinned data/static-history.json.gz")
    check_history(parser.parse_args().archive)
