"""Hash the complete materialized TD arc operands in the MAMUT-ATF-v1 format."""

from decimal import Decimal
from hashlib import sha256
from numbers import Real
from struct import pack

from reference import finite_float


def _binary64(value):
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise ValueError("expected a materialized numeric operand")
    return finite_float(value)


def atf_digest(num_vertices, horizon, arcs):
    """Read (i, j, xs, ys) records in increasing (i, j) order, omitting self arcs."""
    if type(num_vertices) is not int or num_vertices < 1:
        raise ValueError("num_vertices must include the depot")
    lower, upper = map(_binary64, horizon)
    if lower < 0 or upper <= lower:
        raise ValueError("the horizon must satisfy 0 <= start < end")

    digest = sha256(f"MAMUT-ATF-v1\nbinary64\n{num_vertices}\n".encode("ascii"))
    digest.update(pack(">dd", lower, upper))
    records = iter(arcs)
    for i in range(num_vertices):
        for j in range(num_vertices):
            if i == j:
                continue
            try:
                tail, head, xs, ys = next(records)
            except StopIteration:
                raise ValueError(f"missing arc ({i}, {j})") from None
            if type(tail) is not int or type(head) is not int or (tail, head) != (i, j):
                raise ValueError(f"expected directed arc ({i}, {j})")
            count = len(xs)
            if count == 0 or count != len(ys):
                raise ValueError(f"invalid knot count on arc ({i}, {j})")
            if _binary64(xs[0]) != lower or _binary64(xs[-1]) != upper:
                raise ValueError(f"arc ({i}, {j}) must span the declared horizon")
            digest.update(f"{i},{j},{count}\n".encode("ascii"))
            previous_x, previous_y = lower, lower
            for abscissa, ordinate in zip(xs, ys):
                x, y = _binary64(abscissa), _binary64(ordinate)
                if x < previous_x or y < previous_y or y < x:
                    raise ValueError(f"invalid materialized knot on arc ({i}, {j})")
                digest.update(pack(">dd", x, y))
                previous_x, previous_y = x, y
    end = object()
    if next(records, end) is not end:
        raise ValueError("extra arc after the complete directed collection")
    return digest.hexdigest()
