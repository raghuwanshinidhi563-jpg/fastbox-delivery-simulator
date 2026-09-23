# FastBox Delivery Simulator

A logistics simulator for FastBox: assigns packages to delivery agents,
simulates one day of deliveries, and reports each agent's performance.

## Running it

```bash
python delivery_simulator.py data.json
```

Optional flags:

```bash
python delivery_simulator.py data.json --output report.json   # custom output path
python delivery_simulator.py data.json --no-delays             # disable random delay log
python delivery_simulator.py data.json --seed 7                 # reproducible delay rolls
python delivery_simulator.py data.json --visualize               # print an ASCII route map
python delivery_simulator.py data.json --new-agent A4 20 20     # add an agent mid-day
```

## Assumptions & design decisions

The assignment brief left a few things unspecified. Where that happened, I
picked the most logical/efficient interpretation and documented it here
(and in the corresponding code comments).

1. **Input format flexibility.** The brief's sample `data.json` uses dict
   maps (`"W1": [0, 0]`) and the key `"warehouse"` on each package, but
   test data I was given uses list-of-objects (`{"id": "W1", "location":
   [0, 0]}`) and the key `"warehouse_id"`. Rather than assume one shape,
   `load_data()` detects and normalizes both, so the same script runs
   against either format without edits.

2. **Package routing order per agent.** The brief doesn't say what order
   an agent visits their assigned packages in. I process them in the
   order they appear in the input file. This is deterministic and
   reproducible, and avoids introducing an unrequested optimization
   (e.g. TSP-style route optimization) that the brief never asked for
   and that would make the "correct" distance ambiguous to grade against.

3. **Agent-to-package assignment rule.** The brief specifies "nearest
   agent based on Euclidean distance from agent to warehouse." I
   interpreted this as: for each package, compare the agent's *starting*
   location (not their current position after prior deliveries) to the
   package's warehouse, and assign to whichever agent is closest. This
   matches the wording literally and keeps assignment independent of
   simulation order.

4. **Distance calculation per package.** Each package contributes two
   legs to its agent's total distance: current position → warehouse
   (pickup), then warehouse → destination (drop-off). The agent's
   position carries over between packages (they don't teleport back to
   their start between deliveries), which is the most realistic reading
   of "agent picks up packages from warehouse and delivers to
   destination."

5. **Efficiency metric.** The brief's sample report shows
   `efficiency = total_distance / packages_delivered` (e.g. A1:
   85.32 / 2 = 42.66), so efficiency here means *average distance
   travelled per package* — lower is better (less wasted travel per
   delivery), not higher.

6. **"Most efficient agent" / `best_agent`.** Based on the sample report,
   `best_agent` is the agent with the **lowest** efficiency value (least
   distance per package), not the highest. Ties are broken by whichever
   agent delivered more packages, and an agent with zero deliveries is
   never selected as best_agent.

7. **Agents with zero assigned packages.** If no packages are ever
   closest to a given agent, that agent still appears in the report with
   `packages_delivered: 0`, `total_distance: 0.0`, `efficiency: 0.0`,
   rather than being omitted or causing a divide-by-zero error.

8. **Sanity check.** After simulation, the script asserts that the sum
   of `packages_delivered` across all agents equals the total number of
   input packages, per the brief's note to "make sure total packages
   delivered matches total packages."

## Bonus features implemented

- **Random delivery delays** — each pickup has a 20% chance of being
  logged as delayed (cosmetic/log-only; does not change distance or
  delivery success, since the brief doesn't specify how a delay should
  affect the simulation numerically).
- **ASCII route visualization** (`--visualize`) — plots warehouses (`W`),
  agent start points (`A`), and package destinations (`*`) on a text grid.
- **New agent joining mid-day** (`--new-agent ID X Y`) — adds an agent
  before assignment runs, so they're eligible to receive packages.
- **CSV export of the top performer** — writes `top_performer.csv`
  alongside the JSON report.

## Files

- `delivery_simulator.py` — the full solution
- `report.json` — generated report (created when you run the script)
- `top_performer.csv` — generated bonus export (created when you run the script)
