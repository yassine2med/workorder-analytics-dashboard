"""Generate synthetic work orders. Run: python examples/make_sample_data.py"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
BUILDINGS = ["Building A", "Building B", "Building C", "Annex D"]
TRADES = ["HVAC", "Plumbing", "Electrical", "Carpentry", "Custodial"]
VENDORS = ["Acme HVAC", "Northside Plumbing", "Brightline Electric", "Oak and Pine Carpentry", "CleanSweep Services"]
PRIORITY_W = [("Emergency", 5), ("High", 20), ("Medium", 50), ("Low", 25)]
CLOSE_DAYS = {"Emergency": 2, "High": 7, "Medium": 21, "Low": 45}
ISSUES = {
    "HVAC": ["Room too hot", "Thermostat not responding", "Air handler noise", "No cooling"],
    "Plumbing": ["Leaking faucet", "Clogged drain", "Toilet running", "Low water pressure"],
    "Electrical": ["Outlet dead", "Flickering lights", "Breaker tripping", "Exit sign out"],
    "Carpentry": ["Door will not latch", "Ceiling tile stained", "Cabinet hinge broken"],
    "Custodial": ["Spill in corridor", "Restroom restock", "Carpet cleaning request"],
}
AS_OF = date(2026, 11, 1)

rows = []
for i in range(1, 301):
    trade = random.choice(TRADES)
    priority = random.choices([p for p, _ in PRIORITY_W], [w for _, w in PRIORITY_W])[0]
    created = AS_OF - timedelta(days=random.randint(0, 150))
    expected = CLOSE_DAYS[priority] * random.uniform(0.3, 2.2)
    closes = created + timedelta(days=int(expected))
    closed = closes if closes <= AS_OF and random.random() < 0.8 else None
    status = "Closed" if closed else random.choice(["Open", "Open", "In Progress", "On Hold"])
    rows.append({
        "id": f"WO-{1000 + i}",
        "building": random.choice(BUILDINGS),
        "trade": trade,
        "priority": priority,
        "status": status,
        "created": created.isoformat(),
        "closed": closed.isoformat() if closed else "",
        "vendor": VENDORS[TRADES.index(trade)],
        "description": random.choice(ISSUES[trade]),
    })

out = Path(__file__).resolve().parent.parent / "data" / "work_orders.csv"
with out.open("w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"wrote {len(rows)} rows to {out}")
