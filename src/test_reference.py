"""Boundary and independently specified conformance fixtures for version 0.1."""

from fractions import Fraction as Q
import itertools
import json
import math
import unittest

import reference as ref


def document(n=3, weights=None, due=100, services=None, windows=None):
    matrix = [[0 for _ in range(n + 1)] for _ in range(n + 1)]
    if weights is not None:
        for (i, j), x in weights.items():
            matrix[i][j] = x
    d = dict(num_customers=n, depot=0, num_vehicles=None,
             vehicle_capacity=n, demands=[0] + [1] * n, arc_costs=matrix,
             time_windows=windows or [[0, due] for _ in range(n + 1)],
             service_times=services or [0] * (n + 1))
    return json.dumps(d)


def instance(text, profile="binary64-exact-v1", problem="CVRP"):
    return ref.load_instance(text, profile, problem)


class Conformance(unittest.TestCase):
    def test_binary_decimal_interpretations(self):
        token = ref.Token("0.1")
        self.assertEqual(ref.quantity(token, "binary64-exact-v1"),
                         Q(3602879701896397, 36028797018963968))
        self.assertEqual(ref.quantity(token, "decimal-exact-v1"), Q(1, 10))
        self.assertNotEqual(ref.quantity(ref.Token("215.359"), "binary64-exact-v1"),
                            Q(215359, 1000))

    def test_token_preservation_and_duplicate_rejection(self):
        d = ref.read_json('{"id":9007199254740993,"x":1e-3}')
        self.assertEqual(ref.integer(d["id"]), 9007199254740993)
        self.assertEqual(d["x"].text, "1e-3")
        for bad in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                ref.read_json(bad)

    def test_integer_syntax_and_booleans(self):
        for bad in (True, ref.Token("1.0"), ref.Token("1e0"), "1"):
            with self.assertRaises(ValueError):
                ref.integer(bad)
        with self.assertRaises(ValueError):
            ref.quantity(True, "binary64-exact-v1")

    def test_integer_profile_eligibility(self):
        for token in ("0", "1.0", "1e3"):
            self.assertEqual(ref.quantity(ref.Token(token), "integer-exact-v1").denominator, 1)
        with self.assertRaises(ValueError):
            ref.quantity(ref.Token("0.1"), "integer-exact-v1")

    def test_grid_eligibility(self):
        for token in ("75.49", "75.490", "75490e-3"):
            self.assertEqual(ref.quantity(ref.Token(token), "decimal-grid-3-v1"), Q(7549, 100))
        with self.assertRaises(ValueError):
            ref.quantity(ref.Token("0.0001"), "decimal-grid-3-v1")

    def test_subnormals_zero_and_overflow(self):
        self.assertEqual(ref.quantity(ref.Token("5e-324"), "binary64-exact-v1"), Q(1, 2 ** 1074))
        self.assertEqual(ref.quantity(ref.Token("1e-400"), "binary64-exact-v1"), 0)
        self.assertEqual(math.copysign(1, ref.finite_float(-0.0)), 1)
        with self.assertRaises(ValueError):
            ref.quantity(ref.Token("1e400"), "binary64-exact-v1")

    def test_resource_integer_domain(self):
        d = json.loads(document())
        d["vehicle_capacity"] = 9007199254740993
        with self.assertRaises(ValueError):
            instance(json.dumps(d))

    def test_structural_constraints(self):
        i = instance(document())
        for bad in ([[1, 2]], [[1, 2, 2]], [[0, 1, 2, 3]], [[1, 2, 4]],
                    [[], [1, 2, 3]], [[True, 2, 3]]):
            with self.assertRaises(ValueError):
                ref.evaluate(i, bad)
        i["capacity"] = 2
        with self.assertRaises(ValueError):
            ref.evaluate(i, [[1, 2, 3]])
        i["fleet"] = 1
        with self.assertRaises(ValueError):
            ref.evaluate(i, [[1, 2], [3]])

    def test_empty_problem(self):
        result = ref.evaluate(instance(document(n=0)), [])
        self.assertEqual(result["key"], (0,))
        self.assertEqual(result["num_routes"], 0)

    def test_start_deadline_waiting_and_return(self):
        text = document(n=1, weights={(0, 1): 2, (1, 0): 2}, services=[0, 5],
                        windows=[[2, 20], [10, 10]])
        i = instance(text, problem="VRPTW")
        self.assertEqual(ref.evaluate(i, [[1]])["cost"], 4)
        i["windows"][0][1] = Q(16)
        with self.assertRaises(ValueError):
            ref.evaluate(i, [[1]])
        i["windows"][0][1] = Q(17)
        self.assertEqual(ref.evaluate(i, [[1]])["cost"], 4)

    def test_depot_initialization(self):
        for profile in ref.PROFILES:
            for problem in ("CVRP", "VRPTW"):
                with self.subTest(profile=profile, problem=problem):
                    with self.assertRaisesRegex(ValueError, "depot service time must be zero"):
                        instance(document(n=1, services=[3, 0]), profile, problem)
            route = document(n=1, weights={(0, 1): 2}, windows=[[5, 20], [0, 7]])
            self.assertEqual(ref.evaluate(instance(route, profile, "VRPTW"), [[1]])["cost"], 2)
            too_early = document(n=1, weights={(0, 1): 2}, windows=[[5, 20], [0, 6]])
            with self.assertRaisesRegex(ValueError, "time window violated"):
                ref.evaluate(instance(too_early, profile, "VRPTW"), [[1]])

    def test_binary_vs_decimal_temporal_boundary(self):
        text = document(weights={(0, 1): 0.33, (1, 2): 0.56, (2, 3): 0.11}, due=1)
        decimal = instance(text, "decimal-exact-v1", "VRPTW")
        self.assertEqual(ref.evaluate(decimal, [[1, 2, 3]])["cost"], 1)
        with self.assertRaises(ValueError):
            ref.evaluate(instance(text, problem="VRPTW"), [[1, 2, 3]])

    def test_rounded_temporal_accepts_exact_infeasible(self):
        text = document(weights={(0, 1): 2 ** 53, (1, 2): 1, (2, 3): 1}, due=2 ** 53)
        with self.assertRaises(ValueError):
            ref.evaluate(instance(text, problem="VRPTW"), [[1, 2, 3]])
        rounded = instance(text, "canonical-fp64-flat-v1", "VRPTW")
        self.assertEqual(ref.evaluate(rounded, [[1, 2, 3]])["cost"], 2 ** 53)

    def test_exact_objective_preserves_lost_increments(self):
        text = document(weights={(0, 1): 2 ** 53, (1, 2): 1, (2, 3): 1})
        self.assertEqual(ref.evaluate(instance(text), [[1, 2, 3]])["cost"], 2 ** 53 + 2)

    def test_flat_grouped_and_submitted_order(self):
        text = document(weights={(0, 1): 2 ** 53, (0, 2): 1, (2, 3): 1})
        routes = [[1], [2, 3]]
        expected = {"canonical-fp64-flat-v1": 2 ** 53,
                    "canonical-fp64-grouped-v1": 2 ** 53 + 2,
                    "submitted-fp64-flat-v1": 2 ** 53}
        for p, value in expected.items():
            self.assertEqual(ref.evaluate(instance(text, p), routes)["cost"], value)
        submitted = instance(text, "submitted-fp64-flat-v1")
        self.assertEqual(ref.evaluate(submitted, list(reversed(routes)))["cost"], 2 ** 53 + 2)

    def test_exact_permutation_invariance(self):
        text = document(weights={(0, 1): 0.1, (0, 2): 0.2, (0, 3): 0.3})
        for p in ("binary64-exact-v1", "decimal-exact-v1", "decimal-grid-3-v1"):
            i = instance(text, p)
            values = {ref.evaluate(i, list(order))["cost"]
                      for order in itertools.permutations([[1], [2], [3]])}
            self.assertEqual(len(values), 1)

    def test_scaled_integer_equivalence(self):
        text = document(n=1, weights={(0, 1): 0.125, (1, 0): 0.5}, due=1)
        for p, scale in (("binary64-exact-v1", 8), ("decimal-grid-3-v1", 1000)):
            i = instance(text, p, "VRPTW")
            self.assertEqual(ref.scaled_integer_exact(i, [[1]], scale), ref.evaluate(i, [[1]]))
        with self.assertRaises(ValueError):
            ref.scaled_integer_exact(instance(text), [[1]], 10)

    def test_exact_keys_before_display_rounding(self):
        a, b = Q(1), Q(1) + Q(1, 2 ** 54)
        self.assertLess(a, b)
        self.assertEqual(ref.display_cost(a), ref.display_cost(b))
        self.assertEqual(ref.display_decimal(a), ref.display_decimal(b))
        i = instance(document())
        self.assertEqual(ref.evaluate(i, [[1], [2, 3]], "HierarchicalVehicleCost")["key"], (2, 0))

    def test_quantization_ties_and_directions(self):
        for source, answer in (("1.005", "1.00"), ("1.015", "1.02"),
                               ("-1.005", "-1.00"), ("-1.015", "-1.02")):
            self.assertEqual(ref.quantize_decimal(Q(source), 2), Q(answer))
        self.assertEqual(ref.quantize_decimal(Q("-1.019"), 2, "floor"), Q("-1.02"))
        self.assertEqual(ref.quantize_decimal(Q("-1.019"), 2, "toward-zero"), Q("-1.01"))

    def test_display_avoids_double_rounding(self):
        value = Q("1.015") - Q(1, 10 ** 20)
        self.assertEqual(ref.display_decimal(value), "1.01")
        self.assertEqual(ref.display_decimal(Q("1.015")), "1.02")
        self.assertIsNone(ref.display_cost(Q(10 ** 400)))

    def test_exact_record_canonicality(self):
        for q in (Q(0), Q(-1, 3), Q(2 ** 70 + 1, 2 ** 52)):
            self.assertEqual(ref.read_exact_record(ref.exact_record(q)), q)
        for record in ({"numerator": "2", "denominator": "4"},
                       {"numerator": "-0", "denominator": "1"},
                       {"numerator": "0", "denominator": "2"},
                       {"numerator": "1", "denominator": "0"},
                       {"numerator": 1, "denominator": "1"}):
            with self.assertRaises(ValueError):
                ref.read_exact_record(record)

    def test_exact_geometry_midpoints(self):
        self.assertEqual(ref.euclidean_decimal([0, 0], [3, 4], 3), 5)
        self.assertEqual(ref.euclidean_decimal([0, 0], [Q("1.005"), 0], 2), 1)
        self.assertEqual(ref.euclidean_decimal([0, 0], [Q("1.015"), 0], 2), Q("1.02"))
        self.assertEqual(ref.euclidean_decimal([0, 0], [1, 1], 3), Q("1.414"))

    def test_historical_geometry(self):
        self.assertEqual(ref.historical_euclidean([40, 50], [45, 68], "sintef-intcoord"),
                         float("18.681541692269406"))
        self.assertEqual(ref.historical_euclidean([40, 50], [45, 68], "dimacs-intcoord"), 186)

    def test_digest_semantics(self):
        a = [[Q(0), Q(0.1)], [Q(0.1), Q(0)]]
        b = [[Q(0), Q("0.1")], [Q("0.1"), Q(0)]]
        self.assertNotEqual(ref.matrix_digest(a, "decimal"), ref.matrix_digest(b, "decimal"))
        self.assertEqual(ref.matrix_digest([[0.0, -0.0], [0.0, 0.0]], "binary64"),
                         ref.matrix_digest([[0.0, 0.0], [0.0, 0.0]], "binary64"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
