#!/usr/bin/env python3
"""
GPT Leaderboard Simulation
Version: 1.0
Date: 2025-10-02

This script mirrors leaderboard_simulation_v1 but is published under the
name "GPT Simulation" per request. It replays historical trades using the
leaderboard logic from PNL-fomula.sql (3-hour lookback, Top 5 strategies)
and measures realized PNL when executing only the signalled strategy|action
pairs.
"""

from leaderboard_simulation_v1 import (
    run_simulation,
    LOOKBACK_HOURS,
    MIN_WINRATE,
    MIN_SIGNALS,
    MAX_LOSS_ALLOWED,
)

if __name__ == "__main__":
    START_DATE = "2025-10-01 00:00:00"
    END_DATE = "2025-10-02 00:00:00"

    print("=" * 120)
    print("🚀 GPT Leaderboard Simulation (3h lookback, Top 5)")
    print(f"📅 Period: {START_DATE} to {END_DATE}")
    print(
        "🎯 Filters: "
        f"lookback={LOOKBACK_HOURS}h, winrate ≥ {MIN_WINRATE}%, "
        f"signals ≥ {MIN_SIGNALS}, loss streak ≤ {MAX_LOSS_ALLOWED}"
    )
    print("=" * 120)

    results = run_simulation(START_DATE, END_DATE, verbose=True)

    print("\n✅ GPT Simulation complete!")
    print(f"Final PNL: ${results['total_pnl']:.0f}")
