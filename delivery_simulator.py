import json
import math
import random
import csv
import sys
import argparse


def load_data(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)

    warehouses = _to_id_location_dict(data["warehouses"])
    agents = _to_id_location_dict(data["agents"])

    packages = []
    for p in data["packages"]:
        warehouse_id = p.get("warehouse", p.get("warehouse_id"))
        packages.append({
            "id": p["id"],
            "warehouse": warehouse_id,
            "destination": tuple(p["destination"]),
        })

    return warehouses, agents, packages


def _to_id_location_dict(section):
    """Normalize a warehouses/agents section to {id: (x, y)}."""
    if isinstance(section, dict):
        return {k: tuple(v) for k, v in section.items()}
    return {item["id"]: tuple(item["location"]) for item in section}


def euclidean(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)




def assign_packages(agents, warehouses, packages):
    """Nearest-agent assignment: for each package, pick the agent whose
    starting location is closest (Euclidean) to the package's warehouse."""
    assignments = {agent_id: [] for agent_id in agents}
    for pkg in packages:
        warehouse_loc = warehouses[pkg["warehouse"]]
        nearest_agent = min(
            agents,
            key=lambda agent_id: euclidean(agents[agent_id], warehouse_loc)
        )
        assignments[nearest_agent].append(pkg)
    return assignments



def simulate_day(agents, warehouses, assignments, simulate_delays=True, seed=None):
    """Simulate each agent travelling agent -> warehouse -> destination for
    every package they were assigned, accumulating total distance."""
    if seed is not None:
        random.seed(seed)

    report = {}
    delay_log = []

    for agent_id, pkgs in assignments.items():
        current_pos = agents[agent_id]
        total_distance = 0.0
        delivered = 0

        for pkg in pkgs:
            warehouse_loc = warehouses[pkg["warehouse"]]
            destination = pkg["destination"]

            
            total_distance += euclidean(current_pos, warehouse_loc)
            current_pos = warehouse_loc

            
            if simulate_delays and random.random() < 0.2:
                delay_log.append(
                    f"{agent_id} experienced a delay picking up {pkg['id']} at {pkg['warehouse']}"
                )

            
            total_distance += euclidean(current_pos, destination)
            current_pos = destination
            delivered += 1

        efficiency = round(total_distance / delivered, 2) if delivered else 0.0
        report[agent_id] = {
            "packages_delivered": delivered,
            "total_distance": round(total_distance, 2),
            "efficiency": efficiency,
        }

    eligible = {a: r for a, r in report.items() if r["packages_delivered"] > 0}
    if eligible:
        best_agent = min(
            eligible,
            key=lambda a: (eligible[a]["efficiency"], -eligible[a]["packages_delivered"])
        )
    else:
        best_agent = None

    report["best_agent"] = best_agent
    return report, delay_log



def ascii_visualize(warehouses, agents, packages, width=60, height=20):
    all_points = (
        list(warehouses.values())
        + list(agents.values())
        + [p["destination"] for p in packages]
    )
    xs = [pt[0] for pt in all_points]
    ys = [pt[1] for pt in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) or 1
    span_y = (max_y - min_y) or 1

    grid = [[" " for _ in range(width)] for _ in range(height)]

    def place(pt, symbol):
        col = int((pt[0] - min_x) / span_x * (width - 1))
        row = int((pt[1] - min_y) / span_y * (height - 1))
        row = height - 1 - row  # flip so y increases upward
        grid[row][col] = symbol

    for wid, loc in warehouses.items():
        place(loc, "W")
    for aid, loc in agents.items():
        place(loc, "A")
    for pkg in packages:
        place(pkg["destination"], "*")

    lines = ["".join(row) for row in grid]
    legend = "Legend: W = warehouse, A = agent start, * = package destination"
    return "\n".join(lines) + "\n" + legend



def add_new_agent(agents, agent_id, x, y):
    """Add a new agent mid-day; caller should re-run assignment/simulation
    afterwards so the new agent is considered for remaining packages."""
    agents[agent_id] = (x, y)
    return agents



def export_best_agent_csv(report, filepath="top_performer.csv"):
    best_agent = report.get("best_agent")
    if not best_agent:
        return None
    stats = report[best_agent]
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "packages_delivered", "total_distance", "efficiency"])
        writer.writerow([best_agent, stats["packages_delivered"], stats["total_distance"], stats["efficiency"]])
    return filepath



def main():
    parser = argparse.ArgumentParser(description="FastBox delivery simulator")
    parser.add_argument("data_file", help="Path to the input JSON file")
    parser.add_argument("--output", default="report.json", help="Path to write the report JSON")
    parser.add_argument("--new-agent", nargs=3, metavar=("ID", "X", "Y"),
                         help="Add a new agent mid-day, e.g. --new-agent A4 20 20")
    parser.add_argument("--no-delays", action="store_true", help="Disable random delay simulation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible delays")
    parser.add_argument("--visualize", action="store_true", help="Print an ASCII map of the operation")
    args = parser.parse_args()

    warehouses, agents, packages = load_data(args.data_file)

    if args.new_agent:
        agent_id, x, y = args.new_agent
        add_new_agent(agents, agent_id, float(x), float(y))
        print(f"New agent {agent_id} joined at ({x}, {y})")

    assignments = assign_packages(agents, warehouses, packages)
    report, delay_log = simulate_day(
        agents, warehouses, assignments,
        simulate_delays=not args.no_delays, seed=args.seed
    )

    # Sanity check: every package should have been delivered exactly once
    total_delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
    assert total_delivered == len(packages), "Mismatch between packages delivered and total packages!"

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nReport saved to {args.output}")

    if delay_log:
        print("\nDelay log:")
        for entry in delay_log:
            print(f"  - {entry}")

    csv_path = export_best_agent_csv(report)
    if csv_path:
        print(f"Top performer exported to {csv_path}")

    if args.visualize:
        print("\nASCII route map:")
        print(ascii_visualize(warehouses, agents, packages))


if __name__ == "__main__":
    main()
