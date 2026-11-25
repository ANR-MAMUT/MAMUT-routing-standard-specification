"""Check the published synthetic examples without regenerating or rewriting them."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from materialization import atf_digest
import reference as ref
import td_example


ROOT = Path(__file__).resolve().parent.parent


def load(name):
    return json.loads((ROOT / name).read_bytes())


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


class WorkedExamples(unittest.TestCase):
    def envelope(self, prefix, profile, backend):
        manifest_path = prefix + "-instance.manifest.json"
        manifest = load(manifest_path)
        result = load(prefix + "-result.json")
        standard = result["metadata"]["standard"]
        self.assertEqual(manifest["specification"], "mamut-routing/0.1")
        self.assertEqual(standard["specification"], manifest["specification"])
        self.assertEqual(standard["manifest_sha256"], digest(manifest_path))
        for artifact in [manifest["instance"], *manifest["sidecars"]]:
            self.assertEqual(artifact["sha256"], digest(artifact["path"]))
        self.assertEqual(standard["benchmark_revision"], manifest["benchmark_revision"])
        self.assertEqual(standard["objective"], manifest["objective"])
        self.assertEqual(standard["profile"], profile)
        self.assertEqual(manifest["default_profile"], profile)
        self.assertEqual(standard["num_routes"], len(result["routes"]))
        self.assertEqual(standard["routes_sha256"], ref.routes_digest(result["routes"]))
        cost = ref.read_exact_record(standard["authoritative_cost"])
        self.assertEqual(result["cost"], ref.display_cost(cost))
        self.assertIs(standard["display_overflow"], result["cost"] is None)
        evaluation = standard["evaluation"]
        self.assertEqual(evaluation["backend"], backend)
        self.assertEqual(evaluation["source_sha256"], digest(evaluation["checker"]))
        self.assertEqual(evaluation["verification_status"], "incumbent-verified")
        self.assertNotIn("optimality", result["metadata"])
        return manifest, result, standard

    def test_static_binary64(self):
        manifest, result, standard = self.envelope("example", "binary64-exact-v1", "python-fraction")
        instance = ref.load_instance((ROOT / manifest["instance"]["path"]).read_text(),
                                     standard["profile"], manifest["problem"])
        self.assertEqual(ref.matrix_digest(instance["matrix"], "binary64"), manifest["materialization"]["matrix_sha256"])
        cost = ref.evaluate(instance, result["routes"], standard["objective"])["cost"]
        self.assertEqual(cost, Fraction(21617278211378381, 36028797018963968))
        self.assertEqual(ref.read_exact_record(standard["authoritative_cost"]), cost)
        self.assertNotIn("route_evaluations", standard)

    def test_td_earliest_witnesses(self):
        manifest, result, standard = self.envelope("example-td", "td-binary64-exact-v1", "python-fraction-affine-singleton")
        instance = load(manifest["instance"]["path"])
        sidecar = manifest["sidecars"][0]
        self.assertEqual(instance["td"]["atf_sha256"], sidecar["sha256"])
        self.assertEqual(instance["td"]["atf_path"], sidecar["path"])
        atfs = load(sidecar["path"])
        self.assertEqual(atfs["num_customers"], instance["num_customers"])
        self.assertEqual(atfs["horizon"], instance["horizon"])
        identity = atf_digest(instance["num_customers"] + 1, instance["horizon"], atfs["arcs"])
        self.assertEqual(manifest["materialization"]["atf_stream_sha256"], identity)
        self.assertEqual(result["routes"], [[1], [2]])
        computed = td_example.evaluate(instance, atfs, list(reversed(result["routes"])))
        self.assertEqual(computed["route_evaluations"], standard["route_evaluations"])
        self.assertEqual(computed["routes"], result["routes"])
        witnesses = [(ref.read_exact_record(r["duration"]), ref.read_exact_record(r["departure_time"]))
                     for r in standard["route_evaluations"]]
        # Arrival at customer 1 is 1 + 3t/2. Waiting ends when that equals 6.
        # Customer 2 has constant travel time 2 and service window [7, 9].
        self.assertEqual(witnesses, [(Fraction(14, 3), Fraction(10, 3)), (Fraction(6), Fraction(5))])
        expected_cost = Fraction(14, 3) + 6 + 2 * Fraction(5, 4)
        self.assertEqual(ref.read_exact_record(standard["authoritative_cost"]), expected_cost)
        self.assertEqual(computed["cost"], expected_cost)


if __name__ == "__main__":
    unittest.main()
