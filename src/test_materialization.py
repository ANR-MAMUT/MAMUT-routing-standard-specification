"""Known byte streams and complete-graph checks for the materialization encoders."""

import hashlib
import json
from pathlib import Path
import unittest

from materialization import atf_digest
from reference import matrix_digest


VECTORS = json.loads((Path(__file__).resolve().parents[1] / "materialization-vectors.json").read_bytes())


class MaterializationTests(unittest.TestCase):
    def test_published_vectors(self):
        for vector in VECTORS:
            with self.subTest(vector=vector["name"]):
                expected = vector["sha256"]
                self.assertEqual(hashlib.sha256(bytes.fromhex(vector["stream_hex"])).hexdigest(), expected)
                if vector["format"] == "MAMUT-MATRIX-v1":
                    actual = matrix_digest(vector["matrix"], "binary64")
                else:
                    self.assertEqual(vector["format"], "MAMUT-ATF-v1")
                    actual = atf_digest(vector["num_vertices"], vector["horizon"], iter(vector["arcs"]))
                self.assertEqual(actual, expected)

    def test_coverage(self):
        arcs = [(0, 1, [0, 2], [1, 3]), (1, 0, [0, 2], [2, 4])]
        for records in (arcs[:1], arcs[::-1], [arcs[0], arcs[0]], arcs + [arcs[0]], [(0, 0, [0, 2], [0, 2])]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                atf_digest(2, [0, 2], records)

    def test_invalid_knots(self):
        for xs, ys in (([], []), ([0, 1], [0, 1]), ([0, 2], [0]), ([0, 2], [0, 1]),
                       ([0, 1, 1, 2], [0, 3, 2, 4]), ([0, 2], [0, float("nan")])):
            with self.subTest(xs=xs, ys=ys), self.assertRaises(ValueError):
                atf_digest(2, [0, 2], [(0, 1, xs, ys), (1, 0, [0, 2], [1, 3])])


if __name__ == "__main__":
    unittest.main()
