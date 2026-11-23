"""Exact checker for the worked TD fixture's single-customer affine routes."""

from fractions import Fraction

import reference as ref


def exact(value):
    return Fraction(ref.finite_float(value))


def optimize_singleton(instance, arcs, customer):
    """Both legs are affine. The return leg has constant travel time."""
    depot = instance["depot"]
    horizon = tuple(map(exact, instance["horizon"]))
    lower, upper = horizon
    outbound_x, outbound_y = arcs[depot, customer]
    inbound_x, inbound_y = arcs[customer, depot]
    if tuple(outbound_x) != horizon or tuple(inbound_x) != horizon:
        raise ValueError("the worked example requires one affine piece per leg")
    first, last = map(exact, outbound_y)
    rate = (last - first) / (upper - lower)
    return_time = exact(inbound_y[0]) - lower
    if rate <= 0 or exact(inbound_y[1]) - upper != return_time:
        raise ValueError("expected a positive outbound slope and constant return travel time")

    def departure_for(arrival):
        return lower + (arrival - first) / rate

    depot_open, depot_close = map(exact, instance["time_windows"][depot])
    opens, closes = map(exact, instance["time_windows"][customer])
    service = exact(instance["service_times"][customer])
    # Service must finish in time to enter the return arc and reach the depot.
    last_service_start = min(closes, upper - service, depot_close - return_time - service)
    low = max(lower, depot_open)
    high = min(upper, depot_close, departure_for(last_service_start))
    if opens > last_service_start or low > high:
        raise ValueError("infeasible route")

    # Duration is affine on either side of the departure that eliminates waiting.
    candidates = [low, high]
    no_wait = departure_for(opens)
    if low < no_wait < high:
        candidates.append(no_wait)
    choices = []
    for departure in candidates:
        arrival = first + rate * (departure - lower)
        returned = max(opens, arrival) + service + return_time
        choices.append((returned - departure, departure))
    return min(choices)


def evaluate(instance, atfs, submitted_routes):
    resources = dict(n=instance["num_customers"], capacity=instance["vehicle_capacity"],
                     fleet=instance["num_vehicles"], demands=instance["demands"])
    ref.validate_structure(resources, submitted_routes)
    routes = ref.canonical_routes(submitted_routes)
    if any(len(route) != 1 for route in routes):
        raise ValueError("the worked example requires singleton routes")
    arcs = {(i, j): (xs, ys) for i, j, xs, ys in atfs["arcs"]}
    values = [optimize_singleton(instance, arcs, customer) for [customer] in routes]
    total = sum(duration for duration, _ in values) + exact(instance["fleet_fixed_cost"]) * len(routes)
    return dict(routes=routes, cost=total, num_routes=len(routes), route_evaluations=[
        dict(duration=ref.exact_record(duration), departure_time=ref.exact_record(departure))
        for duration, departure in values
    ])
