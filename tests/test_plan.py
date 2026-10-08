import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))
import plan  # noqa: E402

CFG = json.loads((Path(__file__).parent.parent / "config.json").read_text())
TZ = ZoneInfo("Europe/Stockholm")
T0 = datetime(2026, 1, 15, 0, tzinfo=TZ)


def prices_from(values):
    return {T0 + timedelta(hours=i): v for i, v in enumerate(values)}


class BuildPlanTest(unittest.TestCase):
    def test_cheap_hours_preheat_and_expensive_hours_set_back(self):
        prices = prices_from([0.2] * 6 + [1.0] * 6 + [2.5] * 6 + [0.5] * 6)
        rows = plan.build_plan(prices, {}, CFG)
        by_price = {r["price_sek_per_kwh"]: r["setpoint_c"] for r in rows}
        self.assertEqual(by_price[0.2], 16.0)
        self.assertEqual(by_price[2.5], 12.0)

    def test_setpoint_never_outside_limits(self):
        prices = prices_from([0.1, 5.0] * 12)
        for r in plan.build_plan(prices, {}, CFG):
            self.assertGreaterEqual(r["setpoint_c"], CFG["min_c"])
            self.assertLessEqual(r["setpoint_c"], CFG["max_c"])

    def test_flat_prices_hold_base_temperature(self):
        rows = plan.build_plan(prices_from([0.50, 0.52] * 12), {}, CFG)
        self.assertTrue(all(r["setpoint_c"] == CFG["base_c"] for r in rows))

    def test_no_setback_when_very_cold(self):
        prices = prices_from([0.2] * 12 + [3.0] * 12)
        temps = {h: -15.0 for h in prices}
        rows = plan.build_plan(prices, temps, CFG)
        expensive = [r for r in rows if r["price_sek_per_kwh"] == 3.0]
        self.assertTrue(all(r["setpoint_c"] == CFG["base_c"] for r in expensive))

    def test_schedule_merges_consecutive_hours(self):
        rows = plan.build_plan(prices_from([0.2] * 6 + [3.0] * 6 + [1.0] * 12), {}, CFG)
        blocks = plan.to_schedule(rows)
        self.assertLess(len(blocks), len(rows))
        self.assertEqual(blocks[0]["setpoint_c"], 16.0)


if __name__ == "__main__":
    unittest.main()
