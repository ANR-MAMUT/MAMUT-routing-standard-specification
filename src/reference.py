"""Executable reference kernels for MAMUT-routing standard draft 0.1.

This is a specification companion, not a production loader or library patch.
Input is the normalized, materialized static instance described in the document.
"""

from dataclasses import dataclass
from fractions import Fraction as Q
import hashlib
import json
import math
import re
import struct


@dataclass(frozen=True)
class Token:
    text: str


def reject(message):
    raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject("duplicate JSON member: " + key)
        result[key] = value
    return result


def read_json(text):
    """Keep original numeric tokens until their semantic role is known."""
    return json.loads(text, parse_int=Token, parse_float=Token,
                      parse_constant=lambda x: reject("nonfinite: " + x),
                      object_pairs_hook=unique_object)


def integer(value):
    """Structural integers require JSON integer syntax, including large values."""
    if not isinstance(value, Token) or not re.fullmatch(r"-?(0|[1-9][0-9]*)", value.text):
        reject("expected JSON integer token")
    return int(value.text)


PROFILES = {
    "integer-exact-v1": ("binary64", "exact", 1),
    "decimal-exact-v1": ("decimal", "exact", None),
    "decimal-grid-3-v1": ("decimal", "exact", 1000),
    "binary64-exact-v1": ("binary64", "exact", None),
    "canonical-fp64-flat-v1": ("binary64", "flat", None),
    "canonical-fp64-grouped-v1": ("binary64", "grouped", None),
    "submitted-fp64-flat-v1": ("binary64", "submitted", None),
}


def finite_float(value):
    try:
        result = float(value)
    except OverflowError:
        reject("binary64 overflow")
    if not math.isfinite(result):
        reject("binary64 overflow or nonfinite value")
    return 0.0 if result == 0 else result


def quantity(token, profile):
    if not isinstance(token, Token):
        reject("quantity must be a JSON number")
    interpretation, arithmetic, scale = PROFILES[profile]
    if interpretation == "binary64":
        value = finite_float(token.text)
        if scale is not None and (Q(value) * scale).denominator != 1:
            reject("quantity outside declared grid")
        return Q(value) if arithmetic == "exact" else value
    value = Q(token.text)
    if scale is not None and (value * scale).denominator != 1:
        reject("quantity outside declared grid")
    return value


def load_instance(text, profile, problem):
    """Normalize existing field names after external sidecar materialization.

    One matrix supplies both cost and travel time in the current static core.
    Coordinates and unrelated metadata do not define this materialized model.
    """
    if profile not in PROFILES or problem not in ("CVRP", "VRPTW"):
        reject("unsupported profile or problem")
    d = read_json(text)
    n = integer(d["num_customers"])
    if n < 0 or integer(d["depot"]) != 0:
        reject("core requires n >= 0 and depot 0")
    capacity = integer(d["vehicle_capacity"])
    fleet = None if d["num_vehicles"] is None else integer(d["num_vehicles"])
    demands = [integer(x) for x in d["demands"]]
    if any(Q(finite_float(x)) != x for x in [capacity, *demands]):
        reject("resource integer is not exactly representable in binary64")
    if capacity < 0 or (fleet is not None and fleet < 0):
        reject("negative capacity or fleet")
    if len(demands) != n + 1 or demands[0] != 0 or any(x < 0 for x in demands):
        reject("invalid demands")
    matrix = [[quantity(x, profile) for x in row] for row in d["arc_costs"]]
    if len(matrix) != n + 1 or any(len(row) != n + 1 for row in matrix):
        reject("invalid matrix dimensions")
    if any(x < 0 for row in matrix for x in row):
        reject("negative arc")
    if any(matrix[i][i] != 0 for i in range(n + 1)):
        reject("nonzero diagonal")
    windows = services = None
    if problem == "VRPTW" or d.get("service_times") is not None:
        raw_services = d.get("service_times")
        if not isinstance(raw_services, list) or len(raw_services) != n + 1:
            reject("invalid services")
        if quantity(raw_services[0], profile) != 0:
            reject("depot service time must be zero")
    if problem == "VRPTW":
        windows = [[quantity(x, profile) for x in row] for row in d["time_windows"]]
        if len(windows) != n + 1 or any(len(w) != 2 for w in windows):
            reject("invalid windows")
        services = [quantity(x, profile) for x in raw_services]
        if any(x < 0 for x in services):
            reject("invalid services")
        if any(e < 0 or e > l for e, l in windows):
            reject("invalid window bounds")
    return dict(n=n, capacity=capacity, fleet=fleet, demands=demands,
                matrix=matrix, windows=windows, services=services,
                profile=profile, problem=problem)


def solution_routes(text):
    d = read_json(text)
    if not isinstance(d, dict) or not isinstance(d.get("routes"), list):
        reject("expected routes object")
    if any(not isinstance(r, list) for r in d["routes"]):
        reject("expected route arrays")
    return [[integer(v) for v in route] for route in d["routes"]]


def canonical_routes(routes):
    """Call only after validation has excluded empty or duplicate routes."""
    return sorted((list(r) for r in routes), key=lambda r: tuple(r))


def route_arcs(route):
    vertices = [0, *route, 0]
    return zip(vertices, vertices[1:])


def validate_structure(instance, routes):
    n = instance["n"]
    served = []
    for route in routes:
        if not route:
            reject("empty route")
        if any(type(v) is not int or not 1 <= v <= n for v in route):
            reject("invalid customer index")
        served.extend(route)
        if sum(instance["demands"][v] for v in route) > instance["capacity"]:
            reject("capacity exceeded")
    if sorted(served) != list(range(1, n + 1)):
        reject("customer coverage or duplication")
    if instance["fleet"] is not None and len(routes) > instance["fleet"]:
        reject("fleet exceeded")


def add(a, b, approximate):
    return finite_float(a + b) if approximate else a + b


def evaluate(instance, routes, objective="MonoCost"):
    """Return authoritative Q-valued cost and exact lexicographic key.

    A rounded recipe's Q is the exact value of its final binary64 result.
    Invalid input or routes raise ValueError and produce no objective.
    """
    if objective not in ("MonoCost", "HierarchicalVehicleCost"):
        reject("unsupported objective")
    validate_structure(instance, routes)
    arithmetic = PROFILES[instance["profile"]][1]
    approximate = arithmetic != "exact"
    ordered = routes if arithmetic == "submitted" else canonical_routes(routes)
    zero = 0.0 if approximate else 0
    total = zero
    for route in ordered:
        route_cost = zero
        if instance["problem"] == "VRPTW":
            departure = instance["windows"][0][0]
        for i, j in route_arcs(route):
            weight = instance["matrix"][i][j]
            if arithmetic == "grouped":
                route_cost = add(route_cost, weight, approximate)
            else:
                total = add(total, weight, approximate)
            if instance["problem"] == "VRPTW":
                arrival = add(departure, weight, approximate)
                earliest, latest = instance["windows"][j]
                start = max(earliest, arrival)
                if start > latest:
                    reject("time window violated")
                if j != 0:
                    departure = add(start, instance["services"][j], approximate)
        if arithmetic == "grouped":
            total = add(total, route_cost, approximate)
    cost = Q(total)
    key = (len(routes), cost) if objective == "HierarchicalVehicleCost" else (cost,)
    return dict(cost=cost, key=key, num_routes=len(routes),
                routes=[list(r) for r in ordered])


def scaled_integer_exact(instance, routes, scale, objective="MonoCost"):
    """Equivalent evaluator with all temporal and arc quantities in integer units."""
    if type(scale) is not int or scale <= 0:
        reject("invalid scale")
    if PROFILES[instance["profile"]][1] != "exact":
        reject("scaled conversion requires exact interpreted values")

    def scaled(x):
        value = Q(x) * scale
        if value.denominator != 1:
            reject("not on common grid")
        return value.numerator

    converted = dict(instance)
    converted["matrix"] = [[scaled(x) for x in row] for row in instance["matrix"]]
    if instance["windows"] is not None:
        converted["windows"] = [[scaled(x) for x in row] for row in instance["windows"]]
        converted["services"] = [scaled(x) for x in instance["services"]]
    result = evaluate(converted, routes, objective)
    result["cost"] /= scale
    result["key"] = ((len(routes), result["cost"]) if objective == "HierarchicalVehicleCost"
                     else (result["cost"],))
    return result


def round_integer_even(value):
    """Nearest integer, ties to the even integer, valid for either sign."""
    q, r = divmod(value.numerator, value.denominator)
    twice = 2 * r
    return q + int(twice > value.denominator or
                   (twice == value.denominator and q % 2 == 1))


def quantize_decimal(value, digits, direction="nearest-even"):
    """Exact rational quantization. No Decimal context or binary multiplication."""
    if type(digits) is not int or digits < 0:
        reject("digits must be a nonnegative integer")
    scale = 10 ** digits
    scaled = Q(value) * scale
    if direction == "nearest-even":
        integer_value = round_integer_even(scaled)
    elif direction == "floor":
        integer_value = scaled.numerator // scaled.denominator
    elif direction == "toward-zero":
        integer_value = int(scaled)
    else:
        reject("unsupported quantization")
    return Q(integer_value, scale)


def euclidean_decimal(a, b, digits):
    """Optional NEW exact-coordinate geometry recipe, never a historical replacement."""
    if len(a) != 2 or len(b) != 2 or type(digits) is not int or digits < 0:
        reject("expected 2D coordinates and nonnegative decimal precision")
    squared = sum((Q(x) - Q(y)) ** 2 for x, y in zip(a, b, strict=True))
    scale = 10 ** digits
    p, q = squared.numerator * scale * scale, squared.denominator
    k = math.isqrt(p // q)
    comparison = 4 * p - q * (2 * k + 1) ** 2
    k += int(comparison > 0 or (comparison == 0 and k % 2 == 1))
    return Q(k, scale)


def historical_euclidean(a, b, recipe):
    """Provenance recipes under recorded CPython/libm, checked against matrix pins."""
    if recipe in ("sintef-intcoord", "dimacs-intcoord"):
        if any(type(x) is not int for x in (*a, *b)):
            reject("integer coordinates required")
        squared = sum((x - y) ** 2 for x, y in zip(a, b, strict=True))
        value = finite_float(math.sqrt(squared))
        return value if recipe == "sintef-intcoord" else int(finite_float(value * 10.0))
    if recipe == "poryos-mamut-grid3":
        dx = finite_float(finite_float(b[0]) - finite_float(a[0]))
        dy = finite_float(finite_float(b[1]) - finite_float(a[1]))
        return round(finite_float(math.hypot(dx, dy)), 3)
    reject("unknown generation recipe")


def exact_record(value):
    value = Q(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def read_exact_record(record):
    if set(record) != {"numerator", "denominator"}:
        reject("invalid rational record")
    p, q = record["numerator"], record["denominator"]
    if not isinstance(p, str) or not isinstance(q, str):
        reject("rational integers must be strings")
    if not re.fullmatch(r"-?(0|[1-9][0-9]*)", p) or not re.fullmatch(r"[1-9][0-9]*", q):
        reject("invalid rational integer syntax")
    value = Q(int(p), int(q))
    if exact_record(value) != record:
        reject("noncanonical rational record")
    return value


def display_cost(value):
    """RN64 once, nullable only when the exact value overflows binary64."""
    try:
        return finite_float(Q(value))
    except ValueError:
        return None


def display_decimal(value, digits=2):
    rounded = quantize_decimal(Q(value), digits)
    scale = 10 ** digits
    units = int(rounded * scale)
    sign = "-" if units < 0 else ""
    whole, fractional = divmod(abs(units), scale)
    return f"{sign}{whole}.{fractional:0{digits}d}" if digits else sign + str(whole)


def matrix_digest(matrix, interpretation):
    """Hash a specified semantic stream independently of JSON layout/compression."""
    h = hashlib.sha256()
    h.update(f"MAMUT-MATRIX-v1\n{interpretation}\n{len(matrix)}\n".encode("ascii"))
    if any(len(row) != len(matrix) for row in matrix):
        reject("matrix must be square")
    for row in matrix:
        for value in row:
            if interpretation == "binary64":
                h.update(struct.pack(">d", finite_float(value)))
            elif interpretation == "decimal":
                value = Q(value)
                h.update(f"{value.numerator}/{value.denominator}\n".encode("ascii"))
            else:
                reject("unknown matrix interpretation")
    return h.hexdigest()


def routes_digest(routes):
    stream = f"MAMUT-ROUTES-v1\n{len(routes)}\n"
    for route in routes:
        stream += str(len(route)) + ":" + ",".join(str(v) for v in route) + "\n"
    return hashlib.sha256(stream.encode("ascii")).hexdigest()
